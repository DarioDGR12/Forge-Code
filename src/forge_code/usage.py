# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def add(self, other: Usage) -> Usage:
        return Usage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total": self.total,
        }


# USD per 1M tokens: (input, output). Conservative public list prices.
PRICE_TABLE: dict[str, tuple[float, float]] = {
    "gpt-4.1": (2.0, 8.0),
    "gpt-4.1-mini": (0.4, 1.6),
    "gpt-4.1-nano": (0.1, 0.4),
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    "claude-sonnet-4": (3.0, 15.0),
    "claude-opus-4": (15.0, 75.0),
    "claude-3-5-sonnet": (3.0, 15.0),
    "llama-3.3-70b": (0.59, 0.79),
}


def estimate_cost_usd(model: str, usage: Usage) -> float | None:
    key = _price_key(model)
    if key is None:
        return None
    inp, out = PRICE_TABLE[key]
    return (usage.prompt_tokens * inp + usage.completion_tokens * out) / 1_000_000


def _price_key(model: str) -> str | None:
    lowered = model.lower()
    for name in sorted(PRICE_TABLE, key=len, reverse=True):
        if name in lowered:
            return name
    return None


def budget_hit(model: str, usage: Usage, max_usd: float = 0.0, max_tokens: int = 0) -> str:
    """Return a reason if the usage is over the configured budget, else empty."""
    if max_tokens > 0 and usage.total >= max_tokens:
        return f"token budget {usage.total}/{max_tokens}"
    if max_usd > 0:
        cost = estimate_cost_usd(model, usage)
        if cost is not None and cost >= max_usd:
            return f"cost budget ${cost:.4f}/${max_usd:.4f}"
    return ""


def format_budget(
    max_usd: float,
    max_tokens: int,
    turn_usd: float = 0.0,
    turn_tokens: int = 0,
) -> str:
    session: list[str] = []
    if max_usd > 0:
        session.append(f"${max_usd:.4f}")
    if max_tokens > 0:
        session.append(f"{max_tokens} tokens")
    turn: list[str] = []
    if turn_usd > 0:
        turn.append(f"${turn_usd:.4f}")
    if turn_tokens > 0:
        turn.append(f"{turn_tokens} tokens")
    if not session and not turn:
        return "off"
    parts: list[str] = []
    if session:
        parts.append("session " + " / ".join(session))
    if turn:
        parts.append("turn " + " / ".join(turn))
    return " · ".join(parts)


def format_remaining(
    model: str,
    usage: "Usage",
    max_usd: float = 0.0,
    max_tokens: int = 0,
) -> str:
    bits: list[str] = []
    if max_tokens > 0:
        bits.append(f"{max(0, max_tokens - usage.total)} tokens left")
    if max_usd > 0:
        cost = estimate_cost_usd(model, usage)
        if cost is not None:
            bits.append(f"${max(0.0, max_usd - cost):.4f} left")
    return " · ".join(bits)


def format_usage(model: str, usage: Usage) -> str:
    cost = estimate_cost_usd(model, usage)
    bits = [f"{usage.total} tokens ({usage.prompt_tokens} in / {usage.completion_tokens} out)"]
    if cost is not None:
        bits.append(f"${cost:.4f} est.")
    return " · ".join(bits)
