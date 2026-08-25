# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from collections.abc import Callable

from forge_code.config import AppConfig, resolve_api_key
from forge_code.interrupt import CancelFlag
from forge_code.models import Completion, Message
from forge_code.providers import anthropic, openai_compat
from forge_code.retry import with_retry

DeltaFn = Callable[[str], None]


def complete(
    cfg: AppConfig,
    messages: list[Message],
    tools: list[dict[str, Any]],
    on_delta: DeltaFn | None = None,
    cancel: CancelFlag | None = None,
) -> Completion:
    spec = cfg.provider_spec()
    kind = spec.get("kind") or "openai"
    api_key = resolve_api_key(cfg)
    base_url = spec.get("base_url") or ""
    model = cfg.resolved_model()

    def _call() -> Completion:
        if kind == "anthropic":
            if not api_key or api_key == "local":
                raise RuntimeError("Anthropic needs a key. Run: forge auth login anthropic")
            return anthropic.chat(
                base_url=base_url,
                api_key=api_key,
                model=model,
                messages=messages,
                tools=tools,
                stream=bool(cfg.stream and on_delta is not None),
                on_delta=on_delta,
                cancel=cancel,
            )
        if not api_key and spec.get("local") != "true":
            raise RuntimeError(
                f"{cfg.provider} needs a key. Run: forge auth login {cfg.provider}"
            )
        return openai_compat.chat(
            base_url=base_url,
            api_key=api_key or "local",
            model=model,
            messages=messages,
            tools=tools,
            stream=bool(cfg.stream and on_delta is not None),
            on_delta=on_delta,
            cancel=cancel,
        )

    return with_retry(_call, attempts=cfg.retry.attempts, backoff=cfg.retry.backoff)


def list_remote_models(cfg: AppConfig, provider: str | None = None) -> list[str]:
    spec = cfg.provider_spec(provider)
    if spec.get("kind") == "anthropic":
        return [spec.get("default_model") or "claude-sonnet-4-20250514"]
    return openai_compat.list_models(
        spec.get("base_url") or "",
        resolve_api_key(cfg, provider) or "local",
    )


def probe_local() -> dict[str, list[str]]:
    return {
        "ollama": _ollama_tags(),
        "llamacpp": openai_compat.list_models("http://127.0.0.1:8080/v1", "local"),
    }


def _ollama_tags() -> list[str]:
    try:
        request = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
        with urllib.request.urlopen(request, timeout=2) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []
    names: list[str] = []
    for item in body.get("models") or []:
        name = item.get("name") if isinstance(item, dict) else None
        if name:
            names.append(str(name))
    return names
