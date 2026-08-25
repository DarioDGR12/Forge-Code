# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.diffview import preview_writes
from forge_code.undo import checkpoint, remember_write


def test_preview_writes_unified_diff(tmp_path: Path) -> None:
    path = tmp_path / "note.txt"
    path.write_text("hello\n", encoding="utf-8")
    checkpoint(tmp_path, note="turn")
    remember_write(tmp_path, "note.txt", True, "hello\n")
    path.write_text("hola\n", encoding="utf-8")
    diff = preview_writes(tmp_path, ["note.txt"])
    assert "a/note.txt" in diff
    assert "b/note.txt" in diff
    assert "-hello" in diff
    assert "+hola" in diff
