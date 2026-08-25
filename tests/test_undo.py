# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.undo import checkpoint, remember_write, undo_last


def test_file_undo_restores_and_deletes(tmp_path: Path) -> None:
    existing = tmp_path / "keep.txt"
    existing.write_text("old\n", encoding="utf-8")
    checkpoint(tmp_path, note="turn")
    remember_write(tmp_path, "keep.txt", True, "old\n")
    existing.write_text("new\n", encoding="utf-8")
    remember_write(tmp_path, "fresh.txt", False, None)
    (tmp_path / "fresh.txt").write_text("tmp\n", encoding="utf-8")

    message = undo_last(tmp_path)
    assert "undid" in message
    assert existing.read_text(encoding="utf-8") == "old\n"
    assert not (tmp_path / "fresh.txt").exists()
    assert undo_last(tmp_path) == "nothing to undo"
