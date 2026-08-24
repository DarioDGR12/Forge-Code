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


def login(provider: str, api_key: str | None = None, base_url: str | None = None) -> str:
    if provider not in DEFAULT_PROVIDERS and provider != "custom":
        known = ", ".join(sorted(DEFAULT_PROVIDERS))
        raise KeyError(f"unknown provider {provider!r}. known: {known}")
    key = api_key or getpass(f"{provider} API key (empty for local): ").strip()
    creds = load_credentials()
    if key:
        creds[provider] = key
        save_credentials(creds)
    cfg = load_config()
    cfg.provider = provider
    if base_url:
        if provider == "custom":
            cfg.custom_base_url = base_url
        spec = cfg.providers.setdefault(provider, dict(DEFAULT_PROVIDERS.get(provider, {})))
        spec["base_url"] = base_url
        cfg.providers[provider] = spec
    if not cfg.model:
        cfg.model = cfg.provider_spec(provider).get("default_model") or cfg.model
    save_config(cfg)
    return provider


def logout(provider: str) -> None:
    creds = load_credentials()
    creds.pop(provider, None)
    save_credentials(creds)


def status_rows() -> list[tuple[str, str, str]]:
    cfg = load_config()
    rows: list[tuple[str, str, str]] = []
    for name, spec in DEFAULT_PROVIDERS.items():
        key = resolve_api_key(cfg, name)
        if spec.get("local") == "true":
            state = "local" if key else "missing"
        else:
            state = "configured" if key and key != "local" else "missing"
        mark = "*" if name == cfg.provider else ""
        rows.append((f"{name}{mark}", spec.get("base_url", ""), state))
    return rows
