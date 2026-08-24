# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from forge_code.tools.base import ToolSpec
from forge_code.tools.bash import run_bash
from forge_code.tools.fs import edit_file, list_dir, read_file, write_file
from forge_code.tools.search import glob_files, grep_files

STR = {"type": "string"}


class ToolRegistry:
    def __init__(self, tools: Iterable[ToolSpec]):
        self._tools = {tool.name: tool for tool in tools}

    def names(self) -> list[str]:
        return list(self._tools)

    def schemas(self, mode: str = "build") -> list[dict[str, Any]]:
        if mode == "plan":
            return [t.schema() for t in self._tools.values() if not t.writes]
        return [t.schema() for t in self._tools.values()]

    def execute(self, root: Path, name: str, args: dict[str, Any], mode: str = "build") -> str:
        tool = self._tools.get(name)
        if tool is None:
            return f"error: unknown tool {name}"
        if mode == "plan" and (tool.writes or tool.runs_command):
            return "error: plan mode is read-only (switch to /mode build to edit or run commands)"
        try:
            return tool.fn(root, args)
        except PermissionError as exc:
            return f"error: {exc}"
        except OSError as exc:
            return f"error: {exc}"


def default_registry() -> ToolRegistry:
    return ToolRegistry(
        [
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
                    "properties": {
                        "path": STR,
                        "content": STR,
                    },
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
                name="list_dir",
                description="List files and folders in a directory.",
                parameters={"type": "object", "properties": {"path": STR}},
                fn=list_dir,
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
                description="Run a shell command in the workspace. Prefer tests via the QA system when possible.",
                parameters={
                    "type": "object",
                    "properties": {
                        "command": STR,
                        "timeout": {"type": "integer"},
                    },
                    "required": ["command"],
                },
                fn=run_bash,
                runs_command=True,
            ),
        ]
    )
