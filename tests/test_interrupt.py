# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.agent import Agent
from forge_code.config import AppConfig, QAConfig
from forge_code.interrupt import CancelFlag, CancelledError


def test_cancel_flag() -> None:
    flag = CancelFlag()
    flag.check()
    flag.cancel()
    try:
        flag.check()
    except CancelledError:
        pass
    else:
        raise AssertionError("expected CancelledError")
    flag.reset()
    flag.check()


def test_agent_stops_when_cancelled(tmp_path: Path) -> None:
    cancel = CancelFlag()

    def fake_complete(_cfg, _messages, _tools, **_kwargs):
        raise CancelledError("interrupted")

    cfg = AppConfig(provider="ollama", model="local", qa=QAConfig(auto=False))
    agent = Agent(tmp_path, cfg, complete_fn=fake_complete, cancel=cancel)
    result = agent.run([], "hello")
    assert result.interrupted
    assert "Interrupted" in result.text
