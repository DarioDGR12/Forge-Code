# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any

from forge_code.ignore import IgnoreMatcher
from forge_code.tools.base import jail


def tree_dir(root: Path, args: dict[str, Any]) -> str:
    rel = str(args.get("path") or ".")
    depth = int(args.get("depth") or 3)
    start = jail(root, rel)
    if not start.is_dir():
        return f"error: not a directory: {rel}"
    matcher = IgnoreMatcher(root)
    lines: list[str] = [rel.rstrip("/") or "."]
    _walk(root, start, matcher, prefix="", depth=max(1, min(depth, 8)), lines=lines)
    return "\n".join(lines[:400])


def _walk(
    root: Path,
    current: Path,
    matcher: IgnoreMatcher,
    prefix: str,
    depth: int,
    lines: list[str],
) -> None:
    if depth <= 0 or len(lines) >= 400:
        return
    try:
        entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except OSError:
        return
    visible = []
    for entry in entries:
        rel = entry.relative_to(root).as_posix()
        if matcher.ignored(rel + ("/" if entry.is_dir() else "")):
            continue
        visible.append(entry)
    for index, entry in enumerate(visible):
        last = index == len(visible) - 1
        branch = "└── " if last else "├── "
        suffix = "/" if entry.is_dir() else ""
        lines.append(f"{prefix}{branch}{entry.name}{suffix}")
        if entry.is_dir():
            extra = "    " if last else "│   "
            _walk(root, entry, matcher, prefix + extra, depth - 1, lines)
