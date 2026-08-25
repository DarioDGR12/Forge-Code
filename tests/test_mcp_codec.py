# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from forge_code.mcp import decode_stream, encode_message


def test_roundtrip_message() -> None:
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    raw = encode_message(payload)
    message, leftover = decode_stream(raw)
    assert leftover == b""
    assert message == payload


def test_partial_then_complete() -> None:
    payload = {"jsonrpc": "2.0", "id": 2, "result": {"ok": True}}
    raw = encode_message(payload)
    message, buf = decode_stream(raw[:10])
    assert message is None
    message, leftover = decode_stream(buf + raw[10:])
    assert message == payload
    assert leftover == b""
