# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

SYSTEM = """You are Forge, an open-source coding agent that runs in the terminal.
You work inside a single workspace. Use tools to inspect and change that workspace.

Rules:
- Prefer small, correct edits over rewrites.
- Read a file before editing it.
- Never touch secrets (.env, credentials, private keys) or files outside the workspace.
- After meaningful code changes, rely on integrated QA. If QA fails, fix the code.
- Do not pretend tests passed. Use tool output and QA reports.
- In plan mode you may only read and search. Explain the plan; do not edit.
- Speak briefly. Show what you changed and how to verify it.
"""


def load_project_memory(root: Path) -> str:
    chunks: list[str] = []
    for name in ("AGENTS.md", "FORGE.md", ".forge/AGENTS.md"):
        path = root / name
        if path.is_file():
            chunks.append(f"# {name}\n{path.read_text(encoding='utf-8', errors='replace')[:12_000]}")
    return "\n\n".join(chunks)


def system_prompt(root: Path, mode: str) -> str:
    extra = load_project_memory(root)
    parts = [SYSTEM, f"Workspace: {root}", f"Mode: {mode}"]
    if extra:
        parts.append("Project instructions:\n" + extra)
    return "\n\n".join(parts)
