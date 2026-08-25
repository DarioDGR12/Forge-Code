# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from pathlib import Path

from forge_code.config import AppConfig
from forge_code.models import Message
from forge_code.repl import RUN_PREFIX, _slash
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
