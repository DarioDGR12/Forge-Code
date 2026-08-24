# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from forge_code.paths import config_dir

DEFAULT_PROVIDERS: dict[str, dict[str, str]] = {
    "openai": {
        "kind": "openai",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4.1-mini",
        "key_env": "OPENAI_API_KEY",
    },
    "anthropic": {
        "kind": "anthropic",
        "base_url": "https://api.anthropic.com",
        "default_model": "claude-sonnet-4-20250514",
        "key_env": "ANTHROPIC_API_KEY",
    },
    "openrouter": {
        "kind": "openai",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "anthropic/claude-sonnet-4",
        "key_env": "OPENROUTER_API_KEY",
    },
    "groq": {
        "kind": "openai",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "key_env": "GROQ_API_KEY",
    },
    "ollama": {
        "kind": "openai",
        "base_url": "http://127.0.0.1:11434/v1",
        "default_model": "qwen2.5-coder:7b",
        "key_env": "OLLAMA_API_KEY",
        "local": "true",
    },
    "llamacpp": {
        "kind": "openai",
        "base_url": "http://127.0.0.1:8080/v1",
        "default_model": "local",
        "key_env": "LLAMACPP_API_KEY",
        "local": "true",
    },
    "custom": {
        "kind": "openai",
        "base_url": "http://127.0.0.1:8000/v1",
        "default_model": "local",
        "key_env": "FORGE_API_KEY",
        "local": "true",
    },
}


@dataclass
class QAConfig:
    auto: bool = True
    timeout: int = 120


@dataclass
class AppConfig:
    provider: str = "openai"
    model: str = ""
    mode: str = "build"
    qa: QAConfig = field(default_factory=QAConfig)
    providers: dict[str, dict[str, str]] = field(default_factory=lambda: dict(DEFAULT_PROVIDERS))
    custom_base_url: str = ""

    def provider_spec(self, name: str | None = None) -> dict[str, str]:
        key = name or self.provider
        spec = {**DEFAULT_PROVIDERS.get(key, {}), **self.providers.get(key, {})}
        if key == "custom" and self.custom_base_url:
            spec["base_url"] = self.custom_base_url
        env_base = os.environ.get("FORGE_BASE_URL")
        if env_base and key in {"custom", os.environ.get("FORGE_PROVIDER", "")}:
            spec["base_url"] = env_base
        return spec

    def resolved_model(self) -> str:
        if self.model:
            return self.model
        env = os.environ.get("FORGE_MODEL")
        if env:
            return env
        return self.provider_spec().get("default_model") or "gpt-4.1-mini"


def config_path() -> Path:
    return config_dir() / "config.json"


def credentials_path() -> Path:
    return config_dir() / "credentials.json"


def load_config() -> AppConfig:
    raw: dict[str, Any] = {}
    path = config_path()
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
    qa_raw = raw.get("qa") or {}
    providers = dict(DEFAULT_PROVIDERS)
    providers.update(raw.get("providers") or {})
    cfg = AppConfig(
        provider=os.environ.get("FORGE_PROVIDER") or raw.get("provider") or "openai",
        model=raw.get("model") or "",
        mode=raw.get("mode") or "build",
        qa=QAConfig(
            auto=bool(qa_raw.get("auto", True)),
            timeout=int(qa_raw.get("timeout", 120)),
        ),
        providers=providers,
        custom_base_url=raw.get("custom_base_url") or "",
    )
    return cfg


def save_config(cfg: AppConfig) -> None:
    payload = {
        "provider": cfg.provider,
        "model": cfg.model,
        "mode": cfg.mode,
        "qa": asdict(cfg.qa),
        "providers": cfg.providers,
        "custom_base_url": cfg.custom_base_url,
    }
    path = config_path()
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)


def load_credentials() -> dict[str, str]:
    path = credentials_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_credentials(creds: dict[str, str]) -> None:
    path = credentials_path()
    path.write_text(json.dumps(creds, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)


def resolve_api_key(cfg: AppConfig, provider: str | None = None) -> str:
    name = provider or cfg.provider
    creds = load_credentials()
    if creds.get(name):
        return creds[name]
    spec = cfg.provider_spec(name)
    env_name = spec.get("key_env")
    if env_name and os.environ.get(env_name):
        return os.environ[env_name]
    if os.environ.get("FORGE_API_KEY"):
        return os.environ["FORGE_API_KEY"]
    if spec.get("local") == "true":
        return "local"
    return ""
