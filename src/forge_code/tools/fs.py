# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any

from forge_code.tools.base import jail

MAX_READ = 200_000


def read_file(root: Path, args: dict[str, Any]) -> str:
    path = jail(root, str(args["path"]))
    if not path.is_file():
        return f"error: not a file: {args['path']}"
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > MAX_READ:
        text = text[:MAX_READ] + "\n... [truncated]"
    start = int(args.get("offset") or 1)
    limit = args.get("limit")
    lines = text.splitlines()
    sliced = lines[start - 1 : start - 1 + int(limit)] if limit else lines[start - 1 :]
    numbered = [f"{i + start:>4}|{line}" for i, line in enumerate(sliced)]
    return "\n".join(numbered) if numbered else "(empty)"


def write_file(root: Path, args: dict[str, Any]) -> str:
    path = jail(root, str(args["path"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    content = str(args.get("content") or "")
    path.write_text(content, encoding="utf-8")
    _invalidate_pyc(path)
    return f"wrote {args['path']} ({len(content)} bytes)"


def edit_file(root: Path, args: dict[str, Any]) -> str:
    path = jail(root, str(args["path"]))
    if not path.is_file():
        return f"error: not a file: {args['path']}"
    old = str(args.get("old_string") or "")
    new = str(args.get("new_string") or "")
    if not old:
        return "error: old_string is required"
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count == 0:
        return "error: old_string not found"
    if count > 1 and not args.get("replace_all"):
        return f"error: old_string found {count} times; pass replace_all=true or make it unique"
    path.write_text(text.replace(old, new), encoding="utf-8")
    _invalidate_pyc(path)
    return f"edited {args['path']} ({count} replacement{'s' if count != 1 else ''})"


def _invalidate_pyc(path: Path) -> None:
    if path.suffix != ".py":
        return
    cache = path.parent / "__pycache__"
    if not cache.is_dir():
        return
    for item in cache.glob(f"{path.stem}.*"):
        item.unlink(missing_ok=True)


def list_dir(root: Path, args: dict[str, Any]) -> str:
    rel = str(args.get("path") or ".")
    path = jail(root, rel)
    if not path.is_dir():
        return f"error: not a directory: {rel}"
    names = sorted(p.name + ("/" if p.is_dir() else "") for p in path.iterdir())
    return "\n".join(names) if names else "(empty)"
