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
    system = "\n\n".join(m.content for m in messages if m.role == "system")
    converted = _to_anthropic(messages)
    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": 4096,
        "messages": converted,
    }
    if system:
        payload["system"] = system
    if tools:
        payload["tools"] = [_to_anthropic_tool(tool) for tool in tools]
    url = f"{base_url.rstrip('/')}/v1/messages"
    if stream:
        payload["stream"] = True
        return _stream(url, api_key, payload, timeout, on_delta, cancel)
    data = _post(url, api_key, payload, timeout)
    text_parts: list[str] = []
    tool_calls: list[ToolCall] = []
    for i, block in enumerate(data.get("content") or []):
        if block.get("type") == "text":
            text_parts.append(block.get("text") or "")
        elif block.get("type") == "tool_use":
            tool_calls.append(
                ToolCall(
                    id=str(block.get("id") or f"tool_{i}"),
                    name=str(block.get("name") or "unknown"),
                    arguments=block.get("input") or {},
                )
            )
    finish = "tool" if tool_calls or data.get("stop_reason") == "tool_use" else "stop"
    usage_raw = data.get("usage") or {}
    return Completion(
        message=Message(role="assistant", content="".join(text_parts), tool_calls=tool_calls),
        finish=finish,
        usage=Usage(
            prompt_tokens=int(usage_raw.get("input_tokens") or 0),
            completion_tokens=int(usage_raw.get("output_tokens") or 0),
        ),
    )


def parse_anthropic_sse(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line.startswith("data:"):
        return None
    data = line[5:].strip()
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
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    text_parts: list[str] = []
    tool_calls: list[ToolCall] = []
    current_tool: dict[str, Any] | None = None
    usage = Usage()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for raw in response:
                if cancel:
                    cancel.check()
                event = parse_anthropic_sse(raw.decode("utf-8", errors="replace"))
                if not event:
                    continue
                kind = event.get("type")
                if kind == "content_block_start":
                    block = event.get("content_block") or {}
                    if block.get("type") == "tool_use":
                        current_tool = {
                            "id": block.get("id") or f"tool_{len(tool_calls)}",
                            "name": block.get("name") or "unknown",
                            "input": "",
                        }
                elif kind == "content_block_delta":
                    delta = event.get("delta") or {}
                    if delta.get("type") == "text_delta":
                        piece = str(delta.get("text") or "")
                        text_parts.append(piece)
                        if on_delta and piece:
                            on_delta(piece)
                    elif delta.get("type") == "input_json_delta" and current_tool is not None:
                        current_tool["input"] += str(delta.get("partial_json") or "")
                elif kind == "content_block_stop" and current_tool is not None:
                    try:
                        arguments = json.loads(current_tool["input"] or "{}")
                    except json.JSONDecodeError:
                        arguments = {}
                    if not isinstance(arguments, dict):
                        arguments = {}
                    tool_calls.append(
                        ToolCall(
                            id=str(current_tool["id"]),
                            name=str(current_tool["name"]),
                            arguments=arguments,
                        )
                    )
                    current_tool = None
                elif kind == "message_delta":
                    usage_raw = (event.get("usage") or {})
                    usage = Usage(
                        prompt_tokens=int(usage_raw.get("input_tokens") or usage.prompt_tokens),
                        completion_tokens=int(usage_raw.get("output_tokens") or 0),
                    )
    except CancelledError:
        raise
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from Anthropic: {detail[:800]}") from exc
    except KeyboardInterrupt as exc:
        if cancel:
            cancel.cancel()
        raise CancelledError("interrupted") from exc
    return Completion(
        message=Message(role="assistant", content="".join(text_parts), tool_calls=tool_calls),
        finish="tool" if tool_calls else "stop",
        usage=usage,
    )


def _to_anthropic(messages: list[Message]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for message in messages:
        if message.role == "system":
            continue
        if message.role == "tool":
            out.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": message.tool_call_id,
                            "content": message.content,
                        }
                    ],
                }
            )
            continue
        if message.role == "assistant" and message.tool_calls:
            content: list[dict[str, Any]] = []
            if message.content:
                content.append({"type": "text", "text": message.content})
            for call in message.tool_calls:
                content.append(
                    {
                        "type": "tool_use",
                        "id": call.id,
                        "name": call.name,
                        "input": call.arguments,
                    }
                )
            out.append({"role": "assistant", "content": content})
            continue
        out.append({"role": message.role, "content": message.content})
    return out


def _to_anthropic_tool(tool: dict[str, Any]) -> dict[str, Any]:
    function = tool.get("function") or tool
    return {
        "name": function.get("name"),
        "description": function.get("description") or "",
        "input_schema": function.get("parameters") or {"type": "object", "properties": {}},
    }


def _post(url: str, api_key: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from Anthropic: {detail[:800]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"could not reach Anthropic: {exc.reason}") from exc
