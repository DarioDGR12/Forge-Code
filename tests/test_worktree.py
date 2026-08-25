# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

import subprocess
from pathlib import Path

from forge_code.worktree import add_worktree, list_worktrees, remove_worktree


def _git_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("hi\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)


def test_worktree_rejects_bad_names(tmp_path: Path) -> None:
    assert add_worktree(tmp_path, "../x").startswith("error:")
    assert add_worktree(tmp_path, "ok").startswith("error: not a git")


def test_worktree_add_list_remove(tmp_path: Path) -> None:
    _git_repo(tmp_path)
    added = add_worktree(tmp_path, "hotfix")
    assert "hotfix" in added
    dest = tmp_path / ".worktrees" / "hotfix"
    assert dest.is_dir()
    assert (dest / "README.md").is_file()
    rows = list_worktrees(tmp_path)
    assert any("hotfix" in path for path, _extra in rows)
    assert add_worktree(tmp_path, "hotfix").startswith("error: already")
    removed = remove_worktree(tmp_path, "hotfix")
    assert "removed" in removed
    assert not dest.exists()
    assert remove_worktree(tmp_path, "hotfix").startswith("error:")
