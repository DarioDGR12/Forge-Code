# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from forge_code.tools.base import jail
from forge_code.tools.fs import _invalidate_pyc

FILE_RE = re.compile(r"^(---|\+\+\+)\s+[ab]/(.+)$")
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def apply_patch(root: Path, args: dict[str, Any]) -> str:
    diff = str(args.get("diff") or "")
    if not diff.strip():
        return "error: diff is required"
    try:
        applied = _apply(root, diff)
    except ValueError as exc:
        return f"error: {exc}"
    return "applied:\n" + "\n".join(applied) if applied else "error: no file hunks in diff"


def _apply(root: Path, diff: str) -> list[str]:
    lines = diff.splitlines()
    i = 0
    applied: list[str] = []
    while i < len(lines):
        line = lines[i]
        if line.startswith("--- "):
            old_match = FILE_RE.match(line)
            new_match = FILE_RE.match(lines[i + 1]) if i + 1 < len(lines) else None
            if not old_match or not new_match:
                raise ValueError("expected --- a/path and +++ b/path")
            rel = new_match.group(2)
            i += 2
            hunks: list[tuple[int, list[str]]] = []
            while i < len(lines) and lines[i].startswith("@@"):
                header = HUNK_RE.match(lines[i])
                if not header:
                    raise ValueError(f"bad hunk header: {lines[i]}")
                old_start = int(header.group(1))
                i += 1
                body: list[str] = []
                while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("--- "):
                    body.append(lines[i])
                    i += 1
                hunks.append((old_start, body))
            applied.append(_apply_file(root, rel, hunks))
            continue
        i += 1
    return applied


def _apply_file(root: Path, rel: str, hunks: list[tuple[int, list[str]]]) -> str:
    path = jail(root, rel)
    original = path.read_text(encoding="utf-8") if path.is_file() else ""
    source = original.splitlines()
    out: list[str] = []
    cursor = 1
    for old_start, body in hunks:
        if old_start > cursor:
            out.extend(source[cursor - 1 : old_start - 1])
            cursor = old_start
        for row in body:
            if not row:
                continue
            tag, text = row[0], row[1:]
            if tag == " ":
                if cursor - 1 >= len(source) or source[cursor - 1] != text:
                    raise ValueError(f"context mismatch in {rel} at line {cursor}")
                out.append(text)
                cursor += 1
            elif tag == "-":
                if cursor - 1 >= len(source) or source[cursor - 1] != text:
                    raise ValueError(f"delete mismatch in {rel} at line {cursor}")
                cursor += 1
            elif tag == "+":
                out.append(text)
            elif tag == "\\":
                continue
            else:
                raise ValueError(f"unknown diff line: {row}")
    if cursor - 1 < len(source):
        out.extend(source[cursor - 1 :])
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(out)
    if original.endswith("\n") or not original:
        text += "\n"
    path.write_text(text, encoding="utf-8")
    _invalidate_pyc(path)
    return rel
