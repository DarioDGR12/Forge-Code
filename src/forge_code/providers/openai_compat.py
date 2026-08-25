# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from forge_code.interrupt import CancelFlag, CancelledError
from forge_code.models import Completion, Message, ToolCall
from forge_code.usage import Usage

DeltaFn = Callable[[str], None]


def chat(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[Message],
    tools: list[dict[str, Any]],
    timeout: float = 120.0,
    stream: bool = False,
    on_delta: DeltaFn | None = None,
    cancel: CancelFlag | None = None,
) -> Completion:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [message.to_openai() for message in messages],
        "temperature": 0.2,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    url = f"{base_url.rstrip('/')}/chat/completions"
    if stream:
        payload["stream"] = True
        if "openai.com" in url or "openrouter.ai" in url:
            payload["stream_options"] = {"include_usage": True}
        return _stream(url, api_key, payload, timeout, on_delta, cancel)
    data = _post(url, api_key, payload, timeout)
    choice = (data.get("choices") or [{}])[0]
    raw = choice.get("message") or {}
    tool_calls = [_parse_tool_call(item, i) for i, item in enumerate(raw.get("tool_calls") or [])]
    content = raw.get("content") or ""
    finish = "tool" if tool_calls or choice.get("finish_reason") == "tool_calls" else "stop"
    usage_raw = data.get("usage") or {}
    return Completion(
        message=Message(role="assistant", content=content, tool_calls=tool_calls),
        finish=finish,
        usage=Usage(
            prompt_tokens=int(usage_raw.get("prompt_tokens") or 0),
            completion_tokens=int(usage_raw.get("completion_tokens") or 0),
        ),
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


def parse_sse_line(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line.startswith("data:"):
        return None
    data = line[5:].strip()
    if data == "[DONE]":
        return None
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _stream(
    url: str,
    api_key: str,
    payload: dict[str, Any],
    timeout: float,
    on_delta: DeltaFn | None,
    cancel: CancelFlag | None,
) -> Completion:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=_headers(api_key),
        method="POST",
    )
    content: list[str] = []
    calls: dict[int, dict[str, str]] = {}
    usage = Usage()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for raw in response:
                if cancel:
                    cancel.check()
                line = raw.decode("utf-8", errors="replace")
                event = parse_sse_line(line)
                if not event:
                    continue
                usage_raw = event.get("usage") or {}
                if usage_raw:
                    usage = Usage(
                        prompt_tokens=int(usage_raw.get("prompt_tokens") or 0),
                        completion_tokens=int(usage_raw.get("completion_tokens") or 0),
                    )
                choice = (event.get("choices") or [{}])[0]
                delta = choice.get("delta") or {}
                piece = delta.get("content") or ""
                if piece:
                    content.append(piece)
                    if on_delta:
                        on_delta(piece)
                for tc in delta.get("tool_calls") or []:
                    index = int(tc.get("index") or 0)
                    slot = calls.setdefault(index, {"id": "", "name": "", "arguments": ""})
                    if tc.get("id"):
                        slot["id"] = str(tc["id"])
                    function = tc.get("function") or {}
                    if function.get("name"):
                        slot["name"] += str(function["name"])
                    if function.get("arguments"):
                        slot["arguments"] += str(function["arguments"])
    except CancelledError:
        raise
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail[:800]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"could not reach {url}: {exc.reason}") from exc
    except KeyboardInterrupt as exc:
        if cancel:
            cancel.cancel()
        raise CancelledError("interrupted") from exc

    tool_calls = []
    for index, slot in sorted(calls.items()):
        try:
            arguments = json.loads(slot["arguments"] or "{}")
        except json.JSONDecodeError:
            arguments = {"_raw": slot["arguments"]}
        if not isinstance(arguments, dict):
            arguments = {"value": arguments}
        tool_calls.append(
            ToolCall(
                id=slot["id"] or f"call_{index}",
                name=slot["name"] or "unknown",
                arguments=arguments,
            )
        )
    text = "".join(content)
    return Completion(
        message=Message(role="assistant", content=text, tool_calls=tool_calls),
        finish="tool" if tool_calls else "stop",
        usage=usage,
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
