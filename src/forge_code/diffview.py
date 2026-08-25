# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import difflib
from pathlib import Path

from forge_code.undo import load_stack


def visible_diff(root: Path) -> str:
    text = last_diff(root)
    if text:
        return text
    from forge_code.tools.git import git_diff
    from forge_code.undo import is_git

    if not is_git(root):
        return ""
    git = git_diff(root, {})
    if git.startswith("error:") or git in {"", "(clean)"}:
        return ""
    if git.lower().startswith("warning:") or "not a git repository" in git.lower():
        return ""
    return git


def last_diff(root: Path) -> str:
    stack = load_stack(root)
    if not stack:
        return ""
    snap = stack[-1]
    paths = list(dict.fromkeys([*snap.files, *snap.created]))
    return preview_writes(root, paths)


def preview_writes(root: Path, paths: list[str]) -> str:
    chunks: list[str] = []
    stack = load_stack(root)
    snap = stack[-1] if stack else None
    for rel in paths:
        if not rel or rel == "apply_patch":
            continue
        current = root / rel
        new = current.read_text(encoding="utf-8", errors="replace") if current.is_file() else ""
        old = ""
        if snap and rel in snap.files and snap.files[rel] is not None:
            old = snap.files[rel] or ""
        elif snap and rel in snap.created:
            old = ""
        diff = "".join(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}",
            )
        )
        if diff:
            chunks.append(diff)
    return "".join(chunks)[:8000]
