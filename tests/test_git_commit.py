# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

import subprocess
from pathlib import Path

from forge_code.permissions import PermissionGate
from forge_code.tools.git import git_commit
from forge_code.tools.registry import default_registry


def test_git_commit_validates_message_and_paths(tmp_path: Path) -> None:
    assert "message" in git_commit(tmp_path, {"message": "", "paths": ["a"]})
    assert "flag" in git_commit(tmp_path, {"message": "-m sneak", "paths": ["a"]})
    assert "paths" in git_commit(tmp_path, {"message": "ok", "paths": []})
    assert "invalid path" in git_commit(tmp_path, {"message": "ok", "paths": ["../x"]})


def test_git_commit_creates_commit(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("hi\n", encoding="utf-8")
    out = git_commit(tmp_path, {"message": "add a", "paths": ["a.txt"]})
    assert "add a" in out or "files changed" in out or "1 file" in out
    log = subprocess.run(
        ["git", "log", "-1", "--oneline"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "add a" in log.stdout


def test_git_commit_blocks_secret_via_gate(tmp_path: Path) -> None:
    tools = default_registry(PermissionGate(tmp_path))
    result = tools.execute(
        tmp_path, "git_commit", {"message": "leak", "paths": [".env"]}
    )
    assert result.startswith("error:")


def test_git_commit_plan_mode(tmp_path: Path) -> None:
    tools = default_registry()
    result = tools.execute(
        tmp_path, "git_commit", {"message": "x", "paths": ["a"]}, mode="plan"
    )
    assert "read-only" in result
