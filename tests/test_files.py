# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.files import fence_blocks, load_last, read_for_copy, save_turn


def test_save_turn_copies_and_indexes(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "add.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    rels = save_turn(tmp_path, ["src/add.py", "apply_patch", "src/add.py"])
    assert rels == ["src/add.py"]
    copied = tmp_path / "files" / "src" / "add.py"
    assert copied.is_file()
    assert "return a + b" in copied.read_text(encoding="utf-8")
    index = (tmp_path / "files" / "INDEX.md").read_text(encoding="utf-8")
    assert "src/add.py" in index
    assert load_last(tmp_path) == ["src/add.py"]
    path, text = read_for_copy(tmp_path)
    assert path == "src/add.py"
    assert "def add" in text
    blocks = fence_blocks(tmp_path, rels)
    assert "```python" in blocks
    assert "def add" in blocks


def test_read_for_copy_named_path(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("a = 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("b = 2\n", encoding="utf-8")
    save_turn(tmp_path, ["a.py", "b.py"])
    path, text = read_for_copy(tmp_path, "a.py")
    assert path == "a.py"
    assert text == "a = 1\n"
