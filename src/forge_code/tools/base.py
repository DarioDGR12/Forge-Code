# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ToolFn = Callable[[Path, dict[str, Any]], str]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    fn: ToolFn
    writes: bool = False
    runs_command: bool = False

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def jail(root: Path, rel: str) -> Path:
    clean = rel.replace("\\", "/").lstrip("/")
    if ".." in Path(clean).parts:
        raise PermissionError(f"path traversal blocked: {rel}")
    target = (root / clean).resolve()
    base = root.resolve()
    if target != base and base not in target.parents:
        raise PermissionError(f"path escaped workspace: {rel}")
    return target
