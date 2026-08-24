# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.tools.registry import default_registry


def test_read_write_edit_and_jail(tmp_path: Path) -> None:
    tools = default_registry()
    root = tmp_path
    (root / "app.py").write_text("x = 1\n", encoding="utf-8")

    listed = tools.execute(root, "list_dir", {"path": "."})
    assert "app.py" in listed

    text = tools.execute(root, "read_file", {"path": "app.py"})
    assert "x = 1" in text

    wrote = tools.execute(root, "write_file", {"path": "lib/n.py", "content": "n = 2\n"})
    assert "wrote" in wrote
    assert (root / "lib" / "n.py").read_text(encoding="utf-8") == "n = 2\n"

    edited = tools.execute(
        root,
        "edit_file",
        {"path": "app.py", "old_string": "x = 1", "new_string": "x = 3"},
    )
    assert "edited" in edited
    assert (root / "app.py").read_text(encoding="utf-8") == "x = 3\n"

    blocked = tools.execute(root, "read_file", {"path": "../secret"})
    assert blocked.startswith("error:")


def test_plan_mode_blocks_writes(tmp_path: Path) -> None:
    tools = default_registry()
    result = tools.execute(
        tmp_path, "write_file", {"path": "x.py", "content": "1"}, mode="plan"
    )
    assert "read-only" in result
    assert not (tmp_path / "x.py").exists()


def test_grep_and_glob(tmp_path: Path) -> None:
    tools = default_registry()
    (tmp_path / "a.py").write_text("def hello():\n    return 1\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("nope\n", encoding="utf-8")
    found = tools.execute(tmp_path, "glob", {"pattern": "*.py"})
    assert "a.py" in found
    hits = tools.execute(tmp_path, "grep", {"pattern": "def hello"})
    assert "a.py:1" in hits
