# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from forge_code.providers.openai_compat import parse_sse_line


def test_parse_sse_content() -> None:
    event = parse_sse_line('data: {"choices":[{"delta":{"content":"Hi"}}]}')
    assert event is not None
    assert event["choices"][0]["delta"]["content"] == "Hi"


def test_parse_sse_done_and_junk() -> None:
    assert parse_sse_line("data: [DONE]") is None
    assert parse_sse_line("event: message") is None
    assert parse_sse_line("data: not-json") is None
