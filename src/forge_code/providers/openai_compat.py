# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from forge_code.models import Completion, Message, ToolCall


def chat(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[Message],
    tools: list[dict[str, Any]],
    timeout: float = 120.0,
) -> Completion:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [message.to_openai() for message in messages],
        "temperature": 0.2,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    data = _post(f"{base_url.rstrip('/')}/chat/completions", api_key, payload, timeout)
    choice = (data.get("choices") or [{}])[0]
    raw = choice.get("message") or {}
    tool_calls = [_parse_tool_call(item, i) for i, item in enumerate(raw.get("tool_calls") or [])]
    content = raw.get("content") or ""
    finish = "tool" if tool_calls or choice.get("finish_reason") == "tool_calls" else "stop"
    return Completion(
        message=Message(role="assistant", content=content, tool_calls=tool_calls),
        finish=finish,
    )


def list_models(base_url: str, api_key: str, timeout: float = 8.0) -> list[str]:
    url = f"{base_url.rstrip('/')}/models"
    request = urllib.request.Request(
        url,
        headers=_headers(api_key),
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []
    items = body.get("data") or body.get("models") or []
    names: list[str] = []
    for item in items:
        if isinstance(item, dict) and item.get("id"):
            names.append(str(item["id"]))
        elif isinstance(item, str):
            names.append(item)
    return names


def _parse_tool_call(item: dict[str, Any], index: int) -> ToolCall:
    function = item.get("function") or {}
    raw_args = function.get("arguments") or "{}"
    if isinstance(raw_args, dict):
        arguments = raw_args
    else:
        try:
            arguments = json.loads(raw_args)
        except json.JSONDecodeError:
            arguments = {"_raw": raw_args}
    if not isinstance(arguments, dict):
        arguments = {"value": arguments}
    return ToolCall(
        id=str(item.get("id") or f"call_{index}"),
        name=str(function.get("name") or "unknown"),
        arguments=arguments,
    )


def _headers(api_key: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key and api_key != "local":
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _post(url: str, api_key: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=_headers(api_key),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail[:800]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"could not reach {url}: {exc.reason}") from exc
