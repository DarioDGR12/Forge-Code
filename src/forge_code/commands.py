# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

RESERVED = {
    "help",
    "status",
    "tools",
    "model",
    "provider",
    "mode",
    "qa",
    "compact",
    "cost",
    "sessions",
    "resume",
    "export",
    "undo",
    "mcp",
    "bash",
    "clear",
    "init",
    "exit",
    "quit",
    "q",
    "diff",
    "commands",
    "review",
    "memory",
    "ask",
    "retry",
    "last",
    "worktree",
    "alias",
    "budget",
    "share",
    "shares",
    "theme",
    "quiet",
    "find",
    "pin",
    "new",
    "rename",
    "copy",
    "set",
    "api",
    "providers",
    "chat",
    "menu",
    "contribute",
    "contributions",
}

_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")


@dataclass(frozen=True)
class CustomCommand:
    name: str
    body: str
    title: str


def load_commands(root: Path, limit: int = 32) -> dict[str, CustomCommand]:
    folder = root / ".forge" / "commands"
    if not folder.is_dir():
        return {}
    out: dict[str, CustomCommand] = {}
    for path in sorted(folder.glob("*.md")):
        name = path.stem.lower()
        if name in RESERVED or not _NAME.match(name):
            continue
        body = path.read_text(encoding="utf-8", errors="replace").strip()
        if not body:
            continue
        title = _title(body)
        out[name] = CustomCommand(name=name, body=body, title=title)
        if len(out) >= limit:
            break
    return out


def expand_command(command: CustomCommand, args: str) -> str:
    text = command.body
    if "$ARGS" in text or "{{args}}" in text:
        return text.replace("$ARGS", args).replace("{{args}}", args).strip()
    if args:
        return f"{text.rstrip()}\n\n{args}"
    return text


def _title(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()[:80]
        if stripped:
            return stripped[:80]
    return ""
