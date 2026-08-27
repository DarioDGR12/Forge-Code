# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.mentions import expand_mentions


def test_expand_mentions_attaches_file(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "add.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    text = expand_mentions(tmp_path, "fix the tests in @src/add.py please")
    assert "def add(a, b):" in text
    assert "<attached files>" in text
    assert "src/add.py" in text


def test_expand_mentions_line_range_and_email(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")
    text = expand_mentions(tmp_path, "see @note.txt:2-3 and email me@example.com")
    assert "two" in text
    assert "three" in text
    assert "four" not in text.split("<attached files>")[-1]
    assert "email me@example.com" in text


def test_expand_mentions_skips_secrets_and_missing(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("SECRET=1\n", encoding="utf-8")
    text = expand_mentions(tmp_path, "do not leak @.env or @src/nope.py or @todo")
    assert "SECRET=1" not in text
    assert "secret file" in text
    assert "not found" in text
    assert "(@todo" not in text


def test_expand_mentions_blocks_escape(tmp_path: Path) -> None:
    text = expand_mentions(tmp_path, "open @../etc/passwd")
    assert "outside workspace" in text
    assert "root:" not in text
