# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any

MEMORY_REL = Path(".forge") / "memory.md"
MAX_NOTE = 4_000
MAX_READ = 8_000


def memory_path(root: Path) -> Path:
    return root / MEMORY_REL


def load_memory(root: Path, limit: int = MAX_READ) -> str:
    path = memory_path(root)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def memory_read(root: Path, _args: dict[str, Any]) -> str:
    text = load_memory(root)
    return text or "(empty memory)"


def memory_write(root: Path, args: dict[str, Any]) -> str:
    note = str(args.get("note") or "").strip()
    if not note:
        return "error: note is required"
    if note.startswith("--"):
        return "error: note cannot look like a flag"
    note = note.replace("\n", " ")[:MAX_NOTE]
    path = memory_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"- {note}\n")
    return f"remembered {len(note)} chars"
