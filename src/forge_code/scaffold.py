# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

AGENTS_TEMPLATE = """# Agent notes

This file is read by Forge at the start of every session.

## Commands

- Tests:
- Lint:
- Dev server:

## Rules

- Keep changes small.
- Do not commit secrets.
"""

FORGEIGNORE = """# Extra paths Forge should not search (on top of defaults).
.venv/
node_modules/
__pycache__/
.env
.worktrees/
"""

SKILL_PYTHON = """# Python

- Prefer pytest.
- Do not add dependencies unless asked.
- After edits, rely on integrated QA.
"""

COMMAND_EXPLAIN = """# explain

Explain the current change set in plain language.
Use git_status and git_diff. Do not edit.

Focus: $ARGS
"""

COMMAND_TEST = """# test

How should we verify $ARGS?
Use existing tests and integrated QA. Quote tool output. Do not invent results.
If you must edit, keep the change small.
"""

COMMAND_COMMIT = """# commit-msg

Draft a conventional commit message for the current changes.
Use git_status and git_diff. Do not run git_commit. Do not edit files.

Focus: $ARGS
"""

HOOKS_README = """# Hooks

Put executable scripts here (no extension):

- `pre_edit` — before write_file / edit_file / apply_patch (non-zero blocks the edit)
- `post_edit` — after a successful write
- `post_turn` — after the agent finishes

Environment: `FORGE_HOOK`, `FORGE_ROOT`, `FORGE_PATH`, `FORGE_PATHS`, `FORGE_TASK`.
"""


def init_workspace(root: Path) -> list[tuple[str, str]]:
    """Create starter files. Does not overwrite. Returns (relpath, wrote|exists)."""
    planned: list[tuple[Path, str]] = [
        (root / "AGENTS.md", AGENTS_TEMPLATE),
        (root / ".forgeignore", FORGEIGNORE),
        (root / ".forge" / "skills" / "python.md", SKILL_PYTHON),
        (root / ".forge" / "commands" / "explain.md", COMMAND_EXPLAIN),
        (root / ".forge" / "commands" / "test.md", COMMAND_TEST),
        (root / ".forge" / "commands" / "commit-msg.md", COMMAND_COMMIT),
        (root / ".forge" / "hooks" / "README.md", HOOKS_README),
    ]
    results: list[tuple[str, str]] = []
    for path, content in planned:
        rel = path.relative_to(root).as_posix()
        if path.exists():
            results.append((rel, "exists"))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        results.append((rel, "wrote"))
    from forge_code.project import context_path, save_context

    ctx = context_path(root)
    ctx_rel = ctx.relative_to(root).as_posix()
    if ctx.is_file():
        results.append((ctx_rel, "exists"))
    else:
        save_context(root)
        results.append((ctx_rel, "wrote"))
    return results
