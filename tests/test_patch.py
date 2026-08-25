# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.tools.patch import apply_patch


def test_apply_unified_diff(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("hello world\n", encoding="utf-8")
    diff = """--- a/note.txt
+++ b/note.txt
@@ -1,1 +1,1 @@
-hello world
+hola mundo
"""
    result = apply_patch(tmp_path, {"diff": diff})
    assert "note.txt" in result
    assert (tmp_path / "note.txt").read_text(encoding="utf-8") == "hola mundo\n"


def test_apply_rejects_mismatch(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("aaa\n", encoding="utf-8")
    diff = """--- a/note.txt
+++ b/note.txt
@@ -1,1 +1,1 @@
-bbb
+ccc
"""
    result = apply_patch(tmp_path, {"diff": diff})
    assert result.startswith("error:")
    assert (tmp_path / "note.txt").read_text(encoding="utf-8") == "aaa\n"
