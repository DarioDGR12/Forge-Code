# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.journal import append_entry, last_entry, load_journal
from forge_code.qa.runner import QAReport, QAResult, load_last_qa, save_last_qa


def test_append_and_load_newest_first(tmp_path: Path) -> None:
    first = append_entry(tmp_path, task="fix tests", writes=["src/add.py"], qa_ok=False)
    assert first == tmp_path / ".forge" / "journal.md"
    append_entry(tmp_path, task="add README", writes=["README.md", "docs/a.md"], qa_ok=True)
    text = load_journal(tmp_path)
    assert text.index("add README") < text.index("fix tests")
    assert "qa pass" in text
    assert "qa fail" in text
    assert "src/add.py" in text
    newest = last_entry(tmp_path)
    assert "add README" in newest
    assert "fix tests" not in newest
    assert "add README" in load_journal(tmp_path, query="readme")
    assert load_journal(tmp_path, query="zzz-no-hit") == ""


def test_last_qa_roundtrip(tmp_path: Path) -> None:
    assert load_last_qa(tmp_path) is None
    report = QAReport(
        ok=False,
        results=[QAResult(name="pytest", command="pytest", passed=False, output="boom", duration_ms=12)],
    )
    path = save_last_qa(tmp_path, report)
    assert path == tmp_path / ".forge" / "last-qa.json"
    loaded = load_last_qa(tmp_path)
    assert loaded is not None
    assert loaded.ok is False
    assert loaded.results[0].name == "pytest"
    assert loaded.results[0].output == "boom"
