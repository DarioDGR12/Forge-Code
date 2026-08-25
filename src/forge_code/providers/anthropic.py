# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from forge_code.models import Completion, Message, ToolCall
from forge_code.usage import Usage


def chat(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[Message],
    tools: list[dict[str, Any]],
    timeout: float = 120.0,
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
    data = _post(f"{base_url.rstrip('/')}/v1/messages", api_key, payload, timeout)
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
