# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.tools.todo import read_todo, update_todo


def test_todo_roundtrip(tmp_path: Path) -> None:
    text = update_todo(
        tmp_path,
        {
            "items": [
                {"id": "1", "content": "read", "status": "done"},
                {"id": "2", "content": "edit", "status": "in_progress"},
            ]
        },
    )
    assert "[x] 1: read" in text
    assert "[~] 2: edit" in text
    assert "edit" in read_todo(tmp_path, {})
