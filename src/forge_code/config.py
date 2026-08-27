# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from forge_code.mcp import MCPServerConfig
from forge_code.paths import config_dir
from forge_code.permissions import PermissionConfig
from forge_code.providers.catalog import DEFAULT_PROVIDERS, resolve_provider

__all__ = [
    "AppConfig",
    "BudgetConfig",
    "DEFAULT_ALIASES",
    "DEFAULT_PROVIDERS",
    "QAConfig",
    "RetryConfig",
    "resolve_provider",
]


@dataclass
class QAConfig:
    auto: bool = True
    timeout: int = 120
    extra: list[str] = field(default_factory=list)


@dataclass
class RetryConfig:
    attempts: int = 3
    backoff: float = 0.8


DEFAULT_ALIASES: dict[str, str] = {
    "fast": "gpt-4.1-mini",
    "smart": "claude-sonnet-4-20250514",
    "local": "qwen2.5-coder:7b",
}


@dataclass
class BudgetConfig:
    max_usd: float = 0.0
    max_tokens: int = 0
    max_usd_turn: float = 0.0
    max_tokens_turn: int = 0


@dataclass
class AppConfig:
    provider: str = "openai"
    model: str = ""
    mode: str = "build"
    qa: QAConfig = field(default_factory=QAConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    permissions: PermissionConfig = field(default_factory=PermissionConfig)
    providers: dict[str, dict[str, str]] = field(default_factory=lambda: dict(DEFAULT_PROVIDERS))
    custom_base_url: str = ""
    max_steps: int = 24
    compact_after_chars: int = 48_000
    theme: str = "cyan"
    stream: bool = True
    mcp: dict[str, MCPServerConfig] = field(default_factory=dict)
    aliases: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_ALIASES))
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    quiet: bool = False
    lang: str = "auto"

    def provider_spec(self, name: str | None = None) -> dict[str, str]:
        key = name or self.provider
        try:
            key = resolve_provider(key)
        except KeyError:
            pass
        spec = {**DEFAULT_PROVIDERS.get(key, {}), **self.providers.get(key, {})}
        if key == "custom" and self.custom_base_url:
            spec["base_url"] = self.custom_base_url
        env_base = os.environ.get("FORGE_BASE_URL")
        if env_base and key in {"custom", os.environ.get("FORGE_PROVIDER", "")}:
            spec["base_url"] = env_base
        return spec

    def resolved_model(self) -> str:
        if self.model:
            raw = self.model
        else:
            raw = os.environ.get("FORGE_MODEL") or self.provider_spec().get("default_model") or "gpt-4.1-mini"
        return self.aliases.get(raw, raw)


def config_path() -> Path:
    return config_dir() / "config.json"


def credentials_path() -> Path:
    return config_dir() / "credentials.json"


def load_config() -> AppConfig:
    raw: dict[str, Any] = {}
    path = config_path()
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
    raw = {**raw, **_repo_overlay()}
    qa_raw = raw.get("qa") or {}
    retry_raw = raw.get("retry") or {}
    perm_raw = raw.get("permissions") or {}
    budget_raw = raw.get("budget") or {}
    providers = dict(DEFAULT_PROVIDERS)
    providers.update(raw.get("providers") or {})
    if "aliases" in raw and isinstance(raw["aliases"], dict):
        aliases = {str(k): str(v) for k, v in raw["aliases"].items() if k and v}
    else:
        aliases = dict(DEFAULT_ALIASES)
    cfg = AppConfig(
        provider=os.environ.get("FORGE_PROVIDER") or raw.get("provider") or "openai",
        model=raw.get("model") or "",
        mode=raw.get("mode") or "build",
        qa=QAConfig(
            auto=bool(qa_raw.get("auto", True)),
            timeout=int(qa_raw.get("timeout", 120)),
            extra=list(qa_raw.get("extra") or []),
        ),
        retry=RetryConfig(
            attempts=int(retry_raw.get("attempts", 3)),
            backoff=float(retry_raw.get("backoff", 0.8)),
        ),
        permissions=PermissionConfig(
            bash=str(perm_raw.get("bash") or "allow"),
            deny_globs=list(perm_raw.get("deny_globs") or PermissionConfig().deny_globs),
        ),
        providers=providers,
        custom_base_url=raw.get("custom_base_url") or "",
        max_steps=int(raw.get("max_steps") or 24),
        compact_after_chars=int(raw.get("compact_after_chars") or 48_000),
        theme=str(raw.get("theme") or "cyan"),
        stream=bool(raw.get("stream", True)),
        mcp=_parse_mcp(raw.get("mcp") or {}),
        aliases=aliases,
        budget=BudgetConfig(
            max_usd=float(os.environ.get("FORGE_MAX_COST") or budget_raw.get("max_usd") or 0),
            max_tokens=int(os.environ.get("FORGE_MAX_TOKENS") or budget_raw.get("max_tokens") or 0),
            max_usd_turn=float(
                os.environ.get("FORGE_MAX_COST_TURN") or budget_raw.get("max_usd_turn") or 0
            ),
            max_tokens_turn=int(
                os.environ.get("FORGE_MAX_TOKENS_TURN") or budget_raw.get("max_tokens_turn") or 0
            ),
        ),
        quiet=bool(raw.get("quiet", False)),
        lang=_parse_lang(raw.get("lang")),
    )
    from forge_code.i18n import set_config_lang

    set_config_lang(cfg.lang)
    return cfg


def save_config(cfg: AppConfig) -> None:
    payload = {
        "provider": cfg.provider,
        "model": cfg.model,
        "mode": cfg.mode,
        "qa": asdict(cfg.qa),
        "retry": asdict(cfg.retry),
        "permissions": asdict(cfg.permissions),
        "providers": cfg.providers,
        "custom_base_url": cfg.custom_base_url,
        "max_steps": cfg.max_steps,
        "compact_after_chars": cfg.compact_after_chars,
        "theme": cfg.theme,
        "stream": cfg.stream,
        "aliases": cfg.aliases,
        "budget": asdict(cfg.budget),
        "quiet": cfg.quiet,
        "lang": cfg.lang,
        "mcp": {
            name: {"command": spec.command, "args": spec.args, "env": spec.env}
            for name, spec in cfg.mcp.items()
        },
    }
    path = config_path()
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)


def apply_lang(cfg: AppConfig, value: str) -> str:
    from forge_code.i18n import normalize_lang, set_config_lang

    cfg.lang = normalize_lang(value)
    set_config_lang(cfg.lang)
    save_config(cfg)
    return cfg.lang


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


def _parse_mcp(raw: Any) -> dict[str, MCPServerConfig]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, MCPServerConfig] = {}
    for name, spec in raw.items():
        if not isinstance(spec, dict) or not spec.get("command"):
            continue
        out[str(name)] = MCPServerConfig(
            command=str(spec["command"]),
            args=list(spec.get("args") or []),
            env={str(k): str(v) for k, v in (spec.get("env") or {}).items()},
        )
    return out


def _parse_lang(raw: Any) -> str:
    from forge_code.i18n import normalize_lang

    try:
        return normalize_lang(str(raw or "auto"))
    except ValueError:
        return "auto"


def _repo_overlay() -> dict[str, Any]:
    cwd = Path.cwd()
    for candidate in (cwd / ".forge" / "config.json", cwd / "forge.json"):
        if candidate.is_file():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
            if isinstance(data, dict):
                return data
    return {}
