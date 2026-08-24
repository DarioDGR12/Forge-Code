# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

SKIP = {".git", ".venv", "__pycache__", "node_modules", ".forge", "dist", "build"}


def glob_files(root: Path, args: dict[str, Any]) -> str:
    pattern = str(args.get("pattern") or "*")
    matches = [
        p.relative_to(root).as_posix()
        for p in root.rglob(pattern)
        if p.is_file() and not any(part in SKIP for part in p.parts)
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
    hits: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP]
        for name in filenames:
            path = Path(dirpath) / name
            if glob != "*" and not path.match(glob):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if cre.search(line):
                    rel = path.relative_to(root).as_posix()
                    hits.append(f"{rel}:{i}:{line[:240]}")
                    if len(hits) >= 80:
                        return "\n".join(hits) + "\n... (truncated)"
    return "\n".join(hits) if hits else "(no matches)"
