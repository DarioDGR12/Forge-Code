# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from forge_code.models import Message


def estimate_chars(messages: list[Message]) -> int:
    total = 0
    for message in messages:
        total += len(message.content)
        for call in message.tool_calls:
            total += len(call.name) + len(str(call.arguments))
    return total


def compact_messages(messages: list[Message], keep_last: int = 8) -> list[Message]:
    """Drop old tool transcripts; keep system + a short digest + recent turns."""
    if len(messages) <= keep_last + 1:
        return list(messages)
    system = messages[0] if messages and messages[0].role == "system" else None
    body = messages[1:] if system else messages
    if len(body) <= keep_last:
        return list(messages)
    dropped = body[:-keep_last]
    kept = body[-keep_last:]
    digest = _digest(dropped)
    out: list[Message] = []
    if system:
        out.append(system)
    out.append(
        Message(
            role="user",
            content=(
                "Conversation compacted. Earlier work, summarized:\n"
                f"{digest}\n\nContinue from the recent turns."
            ),
        )
    )
    out.extend(kept)
    return out


def _digest(messages: list[Message]) -> str:
    lines: list[str] = []
    for message in messages:
        if message.role == "assistant" and message.content:
            lines.append(f"- assistant: {message.content[:240].replace(chr(10), ' ')}")
        elif message.role == "user" and not message.content.startswith("Integrated QA"):
            lines.append(f"- user: {message.content[:240].replace(chr(10), ' ')}")
        elif message.role == "tool":
            lines.append(f"- tool {message.name}: {message.content[:160].replace(chr(10), ' ')}")
        if len(lines) >= 24:
            lines.append("- …")
            break
    return "\n".join(lines) if lines else "- (no prior content)"
