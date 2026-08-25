# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from pathlib import Path

from forge_code.config import AppConfig
from forge_code.models import Message
from forge_code.repl import RUN_PREFIX, _slash, _slash_alias, _slash_budget, _slash_theme
from forge_code.usage import Usage


def _session(title: str = "") -> SimpleNamespace:
    return SimpleNamespace(id="sess", title=title)


def test_ask_retry_last(tmp_path: Path) -> None:
    cfg = AppConfig(mode="build")
    history = [Message(role="assistant", content="previous answer")]
    session = _session("fix tests")
    totals = Usage()

    empty = _slash("/ask", tmp_path, cfg, history, session, totals)
    assert empty == ""
    assert cfg.mode == "build"

    asked = _slash("/ask where is QA?", tmp_path, cfg, history, session, totals)
    assert asked == RUN_PREFIX + "where is QA?"
    assert cfg.mode == "plan"

    retried = _slash("/retry", tmp_path, cfg, history, session, totals)
    assert retried == RUN_PREFIX + "fix tests"

    last = _slash("/last", tmp_path, cfg, history, _session(), totals)
    assert last == ""

    none = _slash("/retry", tmp_path, cfg, history, _session(), totals)
    assert none == ""
    none_last = _slash("/last", tmp_path, cfg, [], _session(), totals)
    assert none_last == ""


def test_alias_and_budget_slash(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    cfg = AppConfig()
    assert _slash_alias(cfg, "flash gpt-4.1-nano") == ""
    assert cfg.aliases["flash"] == "gpt-4.1-nano"
    assert _slash_alias(cfg, "rm flash") == ""
    assert "flash" not in cfg.aliases
    assert _slash_budget(cfg, "0.25") == ""
    assert cfg.budget.max_usd == 0.25
    assert _slash_budget(cfg, "tokens 100") == ""
    assert cfg.budget.max_tokens == 100
    assert _slash_budget(cfg, "off") == ""
    assert cfg.budget.max_usd == 0
    assert cfg.budget.max_tokens == 0
    assert _slash_budget(cfg, "turn 0.1") == ""
    assert cfg.budget.max_usd_turn == 0.1
    assert _slash_budget(cfg, "turn-tokens 80") == ""
    assert cfg.budget.max_tokens_turn == 80
    assert _slash_budget(cfg, "off") == ""
    assert cfg.budget.max_usd_turn == 0
    assert _slash_theme(cfg, "magenta") == ""
    assert cfg.theme == "magenta"
    assert _slash_theme(cfg, "nope") == ""
    assert cfg.theme == "magenta"


def test_find_and_pin(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    cfg = AppConfig()
    history = [Message(role="assistant", content="use pytest for tests")]
    session = _session()
    empty = _slash("/find", tmp_path, cfg, history, session, Usage())
    assert empty == ""
    none = _slash("/find zzz-no-hit", tmp_path, cfg, history, session, Usage())
    assert none == ""
    pinned = _slash("/pin", tmp_path, cfg, history, session, Usage())
    assert pinned == ""
    mem = (tmp_path / ".forge" / "memory.md").read_text(encoding="utf-8")
    assert "pytest" in mem
    _slash("/pin prefer ruff", tmp_path, cfg, history, session, Usage())
    mem = (tmp_path / ".forge" / "memory.md").read_text(encoding="utf-8")
    assert "ruff" in mem
