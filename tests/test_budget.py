# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.agent import Agent
from forge_code.config import AppConfig, BudgetConfig, QAConfig
from forge_code.models import Completion, Message
from forge_code.usage import Usage, budget_hit, format_budget


def test_budget_hit_tokens_and_cost() -> None:
    usage = Usage(prompt_tokens=100, completion_tokens=0)
    assert budget_hit("gpt-4.1-mini", usage) == ""
    assert "token" in budget_hit("gpt-4.1-mini", usage, max_tokens=50)
    huge = Usage(prompt_tokens=1_000_000, completion_tokens=0)
    assert "cost" in budget_hit("gpt-4.1-mini", huge, max_usd=0.01)
    assert format_budget(0, 0) == "off"
    assert "$" in format_budget(0.5, 0)


def test_agent_stops_on_session_budget(tmp_path: Path) -> None:
    calls = {"n": 0}

    def fake_complete(_cfg, _messages, _tools):
        calls["n"] += 1
        return Completion(
            message=Message(role="assistant", content="more"),
            finish="stop",
            usage=Usage(prompt_tokens=20, completion_tokens=0),
        )

    cfg = AppConfig(
        provider="ollama",
        model="local",
        qa=QAConfig(auto=False),
        budget=BudgetConfig(max_tokens=10),
    )
    agent = Agent(
        tmp_path,
        cfg,
        complete_fn=fake_complete,
        attach_mcp=False,
        session_usage=Usage(prompt_tokens=10, completion_tokens=0),
    )
    result = agent.run([], "continue")
    assert result.budget_hit
    assert calls["n"] == 0
    assert "budget" in result.text.lower()
