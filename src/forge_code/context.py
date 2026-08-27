# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import subprocess
from pathlib import Path

from forge_code.ignore import IgnoreMatcher


def workspace_card(root: Path, limit: int = 80) -> str:
    matcher = IgnoreMatcher(root)
    files: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if not matcher.allowed_file(path):
            continue
        files.append(path.relative_to(root).as_posix())
        if len(files) >= limit:
            files.append("…")
            break
    tree = "\n".join(f"  {name}" for name in files) or "  (empty)"
    git = git_summary(root)
    return f"Tracked files (truncated):\n{tree}\n\nGit:\n{git}"


def git_summary(root: Path) -> str:
    if not (root / ".git").exists() and not _rev_parse(root):
        return "  not a git repository"
    branch = _git(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    status = _git(root, ["status", "--short"])
    lines = [f"  branch: {branch or 'unknown'}"]
    if status:
        for line in status.splitlines()[:20]:
            lines.append(f"  {line}")
    else:
        lines.append("  clean")
    return "\n".join(lines)


def git_recent(root: Path, count: int = 5) -> list[str]:
    text = _git(root, ["log", f"-{max(1, min(count, 12))}", "--oneline"])
    if not text:
        return []
    return [line for line in text.splitlines() if line.strip()]


def _rev_parse(root: Path) -> bool:
    return bool(_git(root, ["rev-parse", "--is-inside-work-tree"]))


def _git(root: Path, args: list[str]) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()
