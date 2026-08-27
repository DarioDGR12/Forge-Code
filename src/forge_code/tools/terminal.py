# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forge_code.tools.base import jail

LOG_REL = Path(".forge") / "terminal.md"
STATE_REL = Path(".forge") / "shell.json"
MAX_ENTRIES = 12
MAX_OUTPUT = 2_000
MAX_READ = 8_000
_SECRET = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|passwd|authorization)\s*[:=]\s*\S+"
)


def load_cwd(root: Path) -> Path:
    rel = str(_state(root).get("cwd") or ".").strip() or "."
    try:
        target = jail(root, rel)
    except PermissionError:
        return root
    return target if target.is_dir() else root


def save_cwd(root: Path, rel: str) -> None:
    path = root / STATE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _state(root)
    payload["cwd"] = rel.strip() or "."
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def log_command(root: Path, command: str, exit_code: int, output: str, cwd: str = ".") -> None:
    safe_cmd = _redact(command.strip())[:500]
    if not safe_cmd:
        return
    body = _redact((output or "")[-MAX_OUTPUT:])
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    entry = f"### exit {exit_code}  cwd {cwd}  {stamp}\n$ {safe_cmd}\n{body}".rstrip()
    existing = load_terminal(root)
    chunks = [chunk.strip() for chunk in existing.split("\n### ") if chunk.strip()]
    rebuilt: list[str] = [entry]
    for chunk in chunks:
        if chunk.startswith("# "):
            continue
        text = chunk if chunk.startswith("### ") else "### " + chunk
        rebuilt.append(text)
        if len(rebuilt) >= MAX_ENTRIES:
            break
    path = root / LOG_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# Forge terminal\n\n"
        "Last shell commands in this workspace. Secrets redacted.\n\n"
    )
    path.write_text(header + "\n\n".join(rebuilt) + "\n", encoding="utf-8")


def load_terminal(root: Path, limit: int = MAX_READ) -> str:
    path = root / LOG_REL
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def terminal_read(root: Path, _args: dict[str, Any]) -> str:
    text = load_terminal(root)
    return text or "(empty terminal log)"


def recent_terminal(root: Path, limit: int = 1_500) -> str:
    text = load_terminal(root)
    if not text:
        return ""
    parts = text.split("\n### ", 1)
    if len(parts) == 1:
        return text[:limit]
    rest = parts[1]
    first, _, more = rest.partition("\n### ")
    chunk = "### " + first
    if more:
        second, _, _ = more.partition("\n### ")
        chunk += "\n### " + second
    return chunk[:limit]


def apply_cd(root: Path, cwd: Path, command: str) -> Path:
    raw = command.strip()
    match = re.match(r"^cd\s+(\S+)$", raw)
    if not match or any(ch in raw for ch in ";|&`$"):
        return cwd
    dest = match.group(1).strip("'\"")
    if dest in {"", "-"} or dest.startswith("-"):
        return cwd
    try:
        candidate = Path(dest).resolve() if Path(dest).is_absolute() else (cwd.resolve() / dest).resolve()
        rel = candidate.relative_to(root.resolve()).as_posix() or "."
        target = jail(root, rel)
    except (PermissionError, ValueError, OSError):
        return cwd
    if target.is_dir():
        save_cwd(root, rel)
        return target
    return cwd


def _state(root: Path) -> dict[str, str]:
    path = root / STATE_REL
    if not path.is_file():
        return {"cwd": "."}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"cwd": "."}
    if not isinstance(raw, dict):
        return {"cwd": "."}
    return {"cwd": str(raw.get("cwd") or ".")}


def _redact(text: str) -> str:
    return _SECRET.sub(lambda m: m.group(1) + "=***", text)
