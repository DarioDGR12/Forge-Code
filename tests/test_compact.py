# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from forge_code.compact import compact_messages, estimate_chars
from forge_code.models import Message


def test_compact_keeps_system_and_recent() -> None:
    messages = [Message(role="system", content="sys")]
    for i in range(20):
        messages.append(Message(role="user" if i % 2 == 0 else "assistant", content=f"m{i}"))
    out = compact_messages(messages, keep_last=6)
    assert out[0].role == "system"
    assert "compacted" in out[1].content.lower()
    assert len(out) < len(messages)
    assert out[-1].content == "m19"


def test_estimate_chars() -> None:
    messages = [Message(role="user", content="abcd")]
    assert estimate_chars(messages) == 4


def test_compact_hard_omits_tool_bodies() -> None:
    messages = [Message(role="system", content="sys")]
    for i in range(12):
        messages.append(Message(role="user", content=f"u{i}"))
        messages.append(
            Message(
                role="tool",
                content="x" * 200,
                name="read_file",
                tool_call_id=str(i),
            )
        )
    out = compact_messages(messages, keep_last=8, hard=True)
    tool_msgs = [m for m in out if m.role == "tool"]
    assert tool_msgs
    assert all("omitted" in m.content for m in tool_msgs)
