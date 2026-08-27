# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from getpass import getpass

from forge_code.config import (
    DEFAULT_PROVIDERS,
    load_config,
    load_credentials,
    resolve_api_key,
    save_config,
    save_credentials,
)
from forge_code.providers.catalog import aliases_for, is_local, resolve_provider


def login(provider: str, api_key: str | None = None, base_url: str | None = None) -> str:
    name = resolve_provider(provider)
    key = api_key if api_key is not None else getpass(f"{name} API key (empty for local): ").strip()
    cfg = load_config()
    apply_provider(cfg, name)
    if base_url:
        if name == "custom":
            cfg.custom_base_url = base_url
        spec = cfg.providers.setdefault(name, dict(DEFAULT_PROVIDERS.get(name, {})))
        spec["base_url"] = base_url
        cfg.providers[name] = spec
        save_config(cfg)
    if key:
        apply_api_key(cfg, key, name)
    return name


def logout(provider: str) -> None:
    name = resolve_provider(provider)
    creds = load_credentials()
    creds.pop(name, None)
    save_credentials(creds)


def apply_provider(cfg, name: str) -> str:
    provider = resolve_provider(name)
    cfg.provider = provider
    cfg.model = cfg.provider_spec(provider).get("default_model") or ""
    save_config(cfg)
    return provider


def apply_api_key(cfg, api_key: str, provider: str | None = None) -> str:
    name = resolve_provider(provider) if provider else cfg.provider
    key = api_key.strip()
    if not key:
        raise ValueError("empty api key")
    creds = load_credentials()
    creds[name] = key
    save_credentials(creds)
    return name


def needs_api_key(cfg, provider: str | None = None) -> bool:
    name = provider or cfg.provider
    spec = cfg.provider_spec(name)
    if is_local(spec):
        return False
    key = resolve_api_key(cfg, name)
    return not key or key == "local"


def status_rows() -> list[tuple[str, str, str]]:
    cfg = load_config()
    rows: list[tuple[str, str, str]] = []
    for name, spec in DEFAULT_PROVIDERS.items():
        key = resolve_api_key(cfg, name)
        if is_local(spec):
            state = "local"
        else:
            state = "configured" if key and key != "local" else "missing"
        mark = "*" if name == cfg.provider else ""
        extra = " ".join(aliases_for(name)[:3])
        label = f"{name}{mark}"
        if extra:
            label = f"{label}  ({extra})"
        rows.append((label, spec.get("base_url", ""), state))
    return rows
