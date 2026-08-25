# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from forge_code.usage import Usage, estimate_cost_usd, format_usage


def test_usage_add_and_cost() -> None:
    left = Usage(prompt_tokens=1_000_000, completion_tokens=0)
    right = Usage(prompt_tokens=0, completion_tokens=1_000_000)
    total = left.add(right)
    assert total.total == 2_000_000
    cost = estimate_cost_usd("gpt-4.1-mini", total)
    assert cost is not None
    assert cost > 0
    text = format_usage("gpt-4.1-mini", total)
    assert "tokens" in text
    assert "$" in text
