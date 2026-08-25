# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.config import DEFAULT_ALIASES, load_config, save_config


def test_default_alias_resolves(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("FORGE_MODEL", raising=False)
    cfg = load_config()
    cfg.model = "fast"
    assert cfg.resolved_model() == DEFAULT_ALIASES["fast"]


def test_alias_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    cfg = load_config()
    cfg.aliases["flash"] = "gpt-4.1-nano"
    save_config(cfg)
    loaded = load_config()
    assert loaded.aliases["flash"] == "gpt-4.1-nano"
    loaded.model = "flash"
    assert loaded.resolved_model() == "gpt-4.1-nano"


def test_env_model_can_be_alias(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("FORGE_MODEL", "local")
    cfg = load_config()
    assert cfg.resolved_model() == DEFAULT_ALIASES["local"]
