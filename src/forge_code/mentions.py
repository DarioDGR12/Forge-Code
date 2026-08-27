# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from pathlib import Path

from forge_code.permissions import SECRET_NAMES
from forge_code.tools.base import jail

MENTION = re.compile(r"(?<!\w)@([^\s]+)")
_RANGE = re.compile(r"^(?P<path>.+):(?P<start>\d+)(?:-(?P<end>\d+))?$")
MAX_FILES = 8
MAX_EACH = 24_000
MAX_TOTAL = 80_000


def expand_mentions(root: Path, text: str) -> str:
    if "@" not in text:
        return text
    attachments: list[str] = []
    seen: set[str] = set()
    total = 0
    for match in MENTION.finditer(text):
        raw = match.group(1).rstrip(".,;:)")
        if not raw or raw in seen or "://" in raw:
            continue
        seen.add(raw)
        if len(attachments) >= MAX_FILES:
            break
        block, used = _attach(root, raw, max(0, MAX_TOTAL - total))
        if not block:
            continue
        attachments.append(block)
        total += used
        if total >= MAX_TOTAL:
            break
    if not attachments:
        return text
    return text.rstrip() + "\n\n<attached files>\n" + "\n\n".join(attachments) + "\n</attached files>\n"


def _attach(root: Path, spec: str, remaining: int) -> tuple[str, int]:
    rel, start, end = _parse_spec(spec)
    try:
        path = jail(root, rel)
    except PermissionError:
        return f"(@{rel} skipped: outside workspace)", 0
    name = path.name
    if name in SECRET_NAMES or name.endswith(".pem"):
        return f"(@{rel} skipped: secret file)", 0
    if not path.exists():
        looks_like_file = "/" in rel.replace("\\", "/") or bool(Path(rel).suffix)
        if looks_like_file:
            return f"(@{rel} not found)", 0
        return "", 0
    if path.is_dir():
        return f"(@{rel} skipped: directory)", 0
    if not path.is_file():
        return "", 0
    try:
        data = path.read_bytes()
    except OSError:
        return f"(@{rel} unreadable)", 0
    if b"\0" in data[:8192]:
        return f"(@{rel} skipped: binary)", 0
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    label = rel
    if start is not None:
        lo = max(1, start)
        hi = end if end is not None else lo
        hi = min(len(lines), max(lo, hi))
        snippet = "\n".join(lines[lo - 1 : hi])
        label = f"{rel}:{lo}-{hi}"
    else:
        snippet = text
    cap = min(MAX_EACH, remaining if remaining else MAX_EACH)
    truncated = len(snippet) > cap
    snippet = snippet[:cap]
    if truncated:
        snippet += "\n... [truncated]"
    fence = "````" if "```" in snippet else "```"
    lang = path.suffix.lstrip(".")
    body = f"{fence}{lang}\n{snippet}\n{fence}"
    return f"### {label}\n{body}", len(snippet)


def _parse_spec(spec: str) -> tuple[str, int | None, int | None]:
    match = _RANGE.fullmatch(spec)
    if not match:
        return spec, None, None
    start = int(match.group("start"))
    end_raw = match.group("end")
    end = int(end_raw) if end_raw else start
    return match.group("path"), start, end
