# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from forge_code.ignore import IgnoreMatcher
from forge_code.tools.base import jail

SKIP = {".git", ".venv", "__pycache__", "node_modules", ".forge", "dist", "build"}


def glob_files(root: Path, args: dict[str, Any]) -> str:
    pattern = str(args.get("pattern") or "*")
    matcher = IgnoreMatcher(root)
    matches = [
        p.relative_to(root).as_posix()
        for p in root.rglob(pattern)
        if p.is_file()
        and not any(part in SKIP for part in p.parts)
        and matcher.allowed_file(p)
    ]
    matches.sort()
    if len(matches) > 200:
        return "\n".join(matches[:200]) + f"\n... ({len(matches) - 200} more)"
    return "\n".join(matches) if matches else "(no matches)"


def grep_files(root: Path, args: dict[str, Any]) -> str:
    query = str(args.get("pattern") or "")
    if not query:
        return "error: pattern is required"
    try:
        cre = re.compile(query)
    except re.error as exc:
        return f"error: invalid regex: {exc}"
    glob = str(args.get("glob") or "*")
    path_arg = str(args.get("path") or "").strip()
    matcher = IgnoreMatcher(root)
    try:
        files = _grep_targets(root, path_arg)
    except PermissionError as exc:
        return f"error: {exc}"
    if isinstance(files, str):
        return files
    hits: list[str] = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        if matcher.ignored(rel):
            continue
        if glob != "*" and not path.match(glob):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if cre.search(line):
                hits.append(f"{rel}:{i}:{line[:240]}")
                if len(hits) >= 80:
                    return "\n".join(hits) + "\n... (truncated)"
    return "\n".join(hits) if hits else "(no matches)"


def _grep_targets(root: Path, path_arg: str) -> list[Path] | str:
    if path_arg:
        start = jail(root, path_arg)
        if start.is_file():
            return [start]
        if not start.is_dir():
            return f"error: not found: {path_arg}"
        walk_root = start
    else:
        walk_root = root
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(walk_root):
        dirnames[:] = [name for name in dirnames if name not in SKIP]
        for name in filenames:
            files.append(Path(dirpath) / name)
    return files
