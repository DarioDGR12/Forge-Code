# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Iterable

from forge_code.permissions import PermissionGate

AskFn = Callable[[str, dict[str, Any]], bool]
from forge_code.tools.base import ToolSpec
from forge_code.tools.bash import run_bash
from forge_code.tools.fs import edit_file, list_dir, read_file, write_file
from forge_code.tools.explore import explore_repo
from forge_code.tools.fetch import fetch_url
from forge_code.tools.git import git_commit, git_diff, git_log, git_status
from forge_code.tools.patch import apply_patch
from forge_code.tools.search import glob_files, grep_files
from forge_code.tools.todo import read_todo, update_todo
from forge_code.tools.tree import tree_dir

STR = {"type": "string"}
WRITE_TOOLS = {"write_file", "edit_file", "apply_patch"}
READ_TOOLS = {"read_file"}


class ToolRegistry:
    def __init__(
        self,
        tools: Iterable[ToolSpec],
        gate: PermissionGate | None = None,
        ask: AskFn | None = None,
    ):
        self._tools = {tool.name: tool for tool in tools}
        self.gate = gate
        self.ask = ask

    def add(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def remove(self, name: str) -> None:
        self._tools.pop(name, None)

    def names(self) -> list[str]:
        return list(self._tools)

    def schemas(self, mode: str = "build") -> list[dict[str, Any]]:
        if mode == "plan":
            return [t.schema() for t in self._tools.values() if not t.writes and not t.runs_command]
        return [t.schema() for t in self._tools.values()]

    def execute(self, root: Path, name: str, args: dict[str, Any], mode: str = "build") -> str:
        tool = self._tools.get(name)
        if tool is None:
            return f"error: unknown tool {name}"
        if mode == "plan" and (tool.writes or tool.runs_command):
            return "error: plan mode is read-only (switch to /mode build to edit or run commands)"
        denied = self._policy(name, args)
        if denied:
            return denied
        try:
            return tool.fn(root, args)
        except PermissionError as exc:
            return f"error: {exc}"
        except OSError as exc:
            return f"error: {exc}"
        except ValueError as exc:
            return f"error: {exc}"

    def _policy(self, name: str, args: dict[str, Any]) -> str | None:
        if self.gate is None:
            return None
        if name in WRITE_TOOLS:
            path = str(args.get("path") or "")
            if name == "apply_patch":
                return None
            decision = self.gate.review_write(path)
            if not decision.allowed:
                return f"error: {decision.reason}"
        if name in READ_TOOLS:
            decision = self.gate.review_read(str(args.get("path") or ""))
            if not decision.allowed:
                return f"error: {decision.reason}"
        if name == "bash":
            decision = self.gate.review_bash(str(args.get("command") or ""))
            if decision.ask:
                command = str(args.get("command") or "")
                if self.ask and self.ask("bash", args):
                    return None
                return f"error: user denied bash: {command}"
            if not decision.allowed:
                return f"error: {decision.reason}"
        if name == "git_commit":
            for rel in args.get("paths") or []:
                decision = self.gate.review_write(str(rel))
                if not decision.allowed:
                    return f"error: {decision.reason}"
        return None


def default_registry(
    gate: PermissionGate | None = None, ask: AskFn | None = None
) -> ToolRegistry:
    return ToolRegistry(_builtin_tools(), gate=gate, ask=ask)


def _builtin_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            name="read_file",
            description="Read a text file in the workspace. Paths are relative to the repo root.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {**STR, "description": "Relative path"},
                    "offset": {"type": "integer", "description": "1-based start line"},
                    "limit": {"type": "integer", "description": "Max lines"},
                },
                "required": ["path"],
            },
            fn=read_file,
        ),
        ToolSpec(
            name="write_file",
            description="Create or overwrite a text file in the workspace.",
            parameters={
                "type": "object",
                "properties": {"path": STR, "content": STR},
                "required": ["path", "content"],
            },
            fn=write_file,
            writes=True,
        ),
        ToolSpec(
            name="edit_file",
            description="Replace old_string with new_string in a file.",
            parameters={
                "type": "object",
                "properties": {
                    "path": STR,
                    "old_string": STR,
                    "new_string": STR,
                    "replace_all": {"type": "boolean"},
                },
                "required": ["path", "old_string", "new_string"],
            },
            fn=edit_file,
            writes=True,
        ),
        ToolSpec(
            name="apply_patch",
            description="Apply a unified diff (--- a/path / +++ b/path) to the workspace.",
            parameters={
                "type": "object",
                "properties": {"diff": {**STR, "description": "Unified diff"}},
                "required": ["diff"],
            },
            fn=apply_patch,
            writes=True,
        ),
        ToolSpec(
            name="list_dir",
            description="List files and folders in a directory.",
            parameters={"type": "object", "properties": {"path": STR}},
            fn=list_dir,
        ),
        ToolSpec(
            name="tree",
            description="Show a depth-limited directory tree, honoring .forgeignore.",
            parameters={
                "type": "object",
                "properties": {
                    "path": STR,
                    "depth": {"type": "integer"},
                },
            },
            fn=tree_dir,
        ),
        ToolSpec(
            name="glob",
            description="Find files by glob pattern, for example **/*.py",
            parameters={
                "type": "object",
                "properties": {"pattern": STR},
                "required": ["pattern"],
            },
            fn=glob_files,
        ),
        ToolSpec(
            name="grep",
            description="Search file contents with a regex.",
            parameters={
                "type": "object",
                "properties": {"pattern": STR, "glob": STR},
                "required": ["pattern"],
            },
            fn=grep_files,
        ),
        ToolSpec(
            name="bash",
            description="Run a shell command in the workspace. Prefer QA for tests.",
            parameters={
                "type": "object",
                "properties": {"command": STR, "timeout": {"type": "integer"}},
                "required": ["command"],
            },
            fn=run_bash,
            runs_command=True,
        ),
        ToolSpec(
            name="git_status",
            description="Show git status --short --branch for the workspace.",
            parameters={"type": "object", "properties": {}},
            fn=git_status,
        ),
        ToolSpec(
            name="git_diff",
            description="Show git diff. Optional path and staged flag.",
            parameters={
                "type": "object",
                "properties": {"path": STR, "staged": {"type": "boolean"}},
            },
            fn=git_diff,
        ),
        ToolSpec(
            name="git_log",
            description="Show recent git commits (oneline).",
            parameters={
                "type": "object",
                "properties": {"count": {"type": "integer"}},
            },
            fn=git_log,
        ),
        ToolSpec(
            name="todo_write",
            description="Replace the session todo list. items: [{id, content, status}]",
            parameters={
                "type": "object",
                "properties": {"items": {"type": "array"}},
                "required": ["items"],
            },
            fn=update_todo,
            writes=True,
        ),
        ToolSpec(
            name="todo_read",
            description="Read the current todo list.",
            parameters={"type": "object", "properties": {}},
            fn=read_todo,
        ),
        ToolSpec(
            name="git_commit",
            description="Stage the given paths and create a git commit. No -a, amend, or hooks skip.",
            parameters={
                "type": "object",
                "properties": {
                    "message": STR,
                    "paths": {"type": "array", "items": STR},
                },
                "required": ["message", "paths"],
            },
            fn=git_commit,
            writes=True,
            runs_command=True,
        ),
        ToolSpec(
            name="fetch_url",
            description="GET a public http(s) URL and return text (docs only, size-capped).",
            parameters={
                "type": "object",
                "properties": {"url": STR},
                "required": ["url"],
            },
            fn=fetch_url,
        ),
        ToolSpec(
            name="explore",
            description="Read-only subagent: search the repo and answer a question. No edits.",
            parameters={
                "type": "object",
                "properties": {"question": STR},
                "required": ["question"],
            },
            fn=explore_repo,
        ),
    ]
