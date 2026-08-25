# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TODO_PATH = Path(".forge") / "todo.json"


def update_todo(root: Path, args: dict[str, Any]) -> str:
    items = args.get("items")
    if not isinstance(items, list):
        return "error: items must be a list of {id, content, status}"
    cleaned: list[dict[str, str]] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        status = str(raw.get("status") or "pending")
        if status not in {"pending", "in_progress", "done"}:
            status = "pending"
        cleaned.append(
            {
                "id": str(raw.get("id") or len(cleaned) + 1),
                "content": str(raw.get("content") or ""),
                "status": status,
            }
        )
    path = root / TODO_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cleaned, indent=2) + "\n", encoding="utf-8")
    return render_todo(cleaned)


def read_todo(root: Path, _args: dict[str, Any]) -> str:
    path = root / TODO_PATH
    if not path.is_file():
        return "(no todos)"
    try:
        items = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "error: todo.json is not valid JSON"
    if not isinstance(items, list):
        return "error: todo.json must be a list"
    return render_todo(items)


def render_todo(items: list[dict[str, str]]) -> str:
    if not items:
        return "(empty todo list)"
    marks = {"pending": "[ ]", "in_progress": "[~]", "done": "[x]"}
    lines = []
    for item in items:
        mark = marks.get(item.get("status", "pending"), "[ ]")
        lines.append(f"{mark} {item.get('id')}: {item.get('content')}")
    return "\n".join(lines)
