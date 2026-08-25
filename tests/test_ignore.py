# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.ignore import IgnoreMatcher


def test_default_ignores_secrets_and_vcs(tmp_path: Path) -> None:
    matcher = IgnoreMatcher(tmp_path)
    assert matcher.ignored(".env")
    assert matcher.ignored("src/__pycache__/x.pyc")
    assert matcher.ignored(".git/config")
    assert not matcher.ignored("src/app.py")


def test_forgeignore_file(tmp_path: Path) -> None:
    (tmp_path / ".forgeignore").write_text("secret-dir/\n*.bak\n", encoding="utf-8")
    matcher = IgnoreMatcher(tmp_path)
    assert matcher.ignored("secret-dir/a.txt")
    assert matcher.ignored("notes.bak")
    assert not matcher.ignored("notes.md")
