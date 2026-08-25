# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

from forge_code.context import workspace_card
from forge_code.skills import load_skills
from forge_code.tools.memory import load_memory

SYSTEM = """You are Forge, an open-source coding agent that runs in the terminal
(Apache 2.0). You work inside a single workspace with tools.

How to work:
- Prefer small, correct edits. Read a file before you change it.
- Use todo_write for multi-step tasks; mark items done as you go.
- Use git_status / git_diff to understand the current tree.
- Use explore for a read-only deep search when the tree is large.
- Use fetch_url only for public documentation (http/https).
- Use memory_write for durable project facts (conventions, decisions). Never store secrets.
- After code changes, trust integrated QA. If QA fails, fix the code.
- Never invent test results. Quote tool output.
- Never touch secrets (.env, keys, credentials) or files outside the workspace.
- In plan mode you may only inspect. Propose a plan; do not edit.
- Speak briefly. Show what changed and how to verify it.
"""


def load_project_memory(root: Path) -> str:
    chunks: list[str] = []
    for name in ("AGENTS.md", "FORGE.md", ".forge/AGENTS.md"):
        path = root / name
        if path.is_file():
            chunks.append(
                f"# {name}\n{path.read_text(encoding='utf-8', errors='replace')[:12_000]}"
            )
    return "\n\n".join(chunks)


def system_prompt(root: Path, mode: str) -> str:
    extra = load_project_memory(root)
    skills = load_skills(root)
    memory = load_memory(root)
    parts = [
        SYSTEM,
        f"Workspace: {root}",
        f"Mode: {mode}",
        workspace_card(root),
    ]
    if extra:
        parts.append("Project instructions:\n" + extra)
    if skills:
        parts.append("Project skills:\n" + skills)
    if memory:
        parts.append("Persistent memory:\n" + memory)
    return "\n\n".join(parts)
