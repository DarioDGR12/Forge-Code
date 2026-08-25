# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from forge_code.undo import is_git

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,47}$")
DIRNAME = ".worktrees"


def worktree_dir(root: Path, name: str) -> Path:
    return (root / DIRNAME / name).resolve()


def add_worktree(root: Path, name: str) -> str:
    bad = _name_error(name)
    if bad:
        return bad
    if not is_git(root):
        return "error: not a git repository"
    dest = worktree_dir(root, name)
    if root.resolve() not in dest.parents:
        return "error: path escaped workspace"
    if dest.exists():
        return f"error: already exists: {dest}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    branch = f"forge/{name}"
    code, out = _git(root, ["worktree", "add", "-b", branch, str(dest)])
    if code != 0:
        if dest.exists():
            return f"error: {out}"
        code, out = _git(root, ["worktree", "add", str(dest), branch])
        if code != 0:
            return f"error: {out}"
    return f"worktree {name} → {dest} (branch {branch})"


def list_worktrees(root: Path) -> list[tuple[str, str]]:
    if not is_git(root):
        return []
    code, out = _git(root, ["worktree", "list"])
    if code != 0 or not out:
        return []
    rows: list[tuple[str, str]] = []
    for line in out.splitlines():
        parts = line.split()
        if not parts:
            continue
        path = parts[0]
        extra = " ".join(parts[1:])
        rows.append((path, extra))
    return rows


def remove_worktree(root: Path, name: str) -> str:
    bad = _name_error(name)
    if bad:
        return bad
    if not is_git(root):
        return "error: not a git repository"
    dest = worktree_dir(root, name)
    if not dest.exists():
        return f"error: no worktree named {name}"
    code, out = _git(root, ["worktree", "remove", str(dest)])
    if code != 0:
        return f"error: {out}"
    return f"removed worktree {name}"


def _name_error(name: str) -> str:
    name = name.strip()
    if not name or not _NAME.match(name) or ".." in name:
        return "error: name must be letters, digits, '.', '_' or '-' (no '..')"
    return ""


def _git(root: Path, args: list[str]) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    text = ((completed.stdout or "") + (completed.stderr or "")).strip()
    return completed.returncode, text
