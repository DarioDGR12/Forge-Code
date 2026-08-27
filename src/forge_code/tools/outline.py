# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

"""List symbols in a file without dumping the whole buffer."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from forge_code.tools.base import jail

MAX_READ = 200_000
MAX_HITS = 200
# def / class / fn / func / function plus common TS/Go/Rust/Java forms
_SYMBOL = re.compile(
    r"^\s*(?:(?:export|pub(?:\(crate\))?|async|public|private|protected|static|default)\s+)*"
    r"(?:def|class|fn|func|function|interface|type|struct|enum|impl|trait)\b"
    r".+"
)


def outline_file(root: Path, args: dict[str, Any]) -> str:
    rel = str(args.get("path") or "").strip()
    if not rel:
        return "error: path is required"
    path = jail(root, rel)
    if not path.is_file():
        return f"error: not a file: {rel}"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"error: {exc}"
    if len(text) > MAX_READ:
        text = text[:MAX_READ]
    hits: list[str] = []
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//", "/*", "*")):
            continue
        if _SYMBOL.match(line):
            hits.append(f"{i}:{stripped[:160]}")
            if len(hits) >= MAX_HITS:
                hits.append("... (truncated)")
                break
    return "\n".join(hits) if hits else "(no symbols)"
