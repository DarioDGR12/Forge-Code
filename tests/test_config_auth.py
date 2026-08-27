# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code import auth, config


def test_byok_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("FORGE_API_KEY", raising=False)
    monkeypatch.delenv("FORGE_PROVIDER", raising=False)

    auth.login("openai", api_key="sk-test-123")
    cfg = config.load_config()
    assert cfg.provider == "openai"
    assert config.resolve_api_key(cfg) == "sk-test-123"

    auth.logout("openai")
    cfg = config.load_config()
    assert config.resolve_api_key(cfg) == ""


def test_set_provider_and_api_alias(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.delenv("FORGE_API_KEY", raising=False)
    monkeypatch.delenv("FORGE_PROVIDER", raising=False)

    auth.apply_provider(config.load_config(), "mistralai")
    cfg = config.load_config()
    assert cfg.provider == "mistral"
    assert "codestral" in cfg.resolved_model()
    auth.apply_api_key(cfg, "sk-test-mistral")
    assert config.resolve_api_key(cfg) == "sk-test-mistral"
    assert auth.needs_api_key(cfg) is False


def test_local_ollama_needs_no_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    monkeypatch.delenv("FORGE_API_KEY", raising=False)
    cfg = config.load_config()
    assert config.resolve_api_key(cfg, "ollama") == "local"


def test_lang_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("FORGE_LANG", raising=False)
    cfg = config.load_config()
    assert cfg.lang == "auto"
    config.apply_lang(cfg, "es")
    assert config.load_config().lang == "es"
    config.apply_lang(cfg, "auto")
    assert config.load_config().lang == "auto"


def test_env_overrides_provider(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("FORGE_PROVIDER", "groq")
    monkeypatch.setenv("FORGE_MODEL", "llama-3.3-70b-versatile")
    cfg = config.load_config()
    assert cfg.provider == "groq"
    assert cfg.resolved_model() == "llama-3.3-70b-versatile"
