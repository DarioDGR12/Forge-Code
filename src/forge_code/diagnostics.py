# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Diagnostic:
    path: str
    message: str
    tool: str

    def format(self) -> str:
        return f"{self.path}: {self.message}"


def run_diagnostics(root: Path, paths: list[str], timeout: int = 45) -> list[Diagnostic]:
    unique = [item for item in dict.fromkeys(paths) if item and item != "apply_patch"]
    found: list[Diagnostic] = []
    py = [p for p in unique if p.endswith(".py")]
    ts = [p for p in unique if p.endswith((".ts", ".tsx", ".js", ".jsx"))]
    go = [p for p in unique if p.endswith(".go")]
    if py:
        found.extend(_run_py(root, py, timeout))
    if ts:
        found.extend(_run_ts(root, timeout))
    if go:
        found.extend(_run_go(root, go, timeout))
    return found


def format_diagnostics(items: list[Diagnostic]) -> str:
    if not items:
        return "LSP: no diagnostics"
    lines = ["LSP: issues after edits"]
    lines.extend(f"  - {item.format()}" for item in items[:40])
    return "\n".join(lines)


def _run_py(root: Path, paths: list[str], timeout: int) -> list[Diagnostic]:
    if shutil.which("pyright"):
        return _collect(root, ["pyright", "--outputjson", *paths], timeout, "pyright", _parse_pyright)
    if shutil.which("ruff"):
        return _collect(root, ["ruff", "check", *paths], timeout, "ruff", _parse_lines)
    return []


def _run_ts(root: Path, timeout: int) -> list[Diagnostic]:
    if not (root / "tsconfig.json").exists():
        return []
    tsc = shutil.which("tsc")
    if not tsc:
        return []
    return _collect(root, [tsc, "--noEmit", "--pretty", "false"], timeout, "tsc", _parse_lines)


def _run_go(root: Path, paths: list[str], timeout: int) -> list[Diagnostic]:
    if not shutil.which("go"):
        return []
    return _collect(root, ["go", "vet", *paths], timeout, "go vet", _parse_lines)


def _collect(root: Path, command: list[str], timeout: int, tool: str, parser) -> list[Diagnostic]:
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode == 0:
        return []
    return parser(output, tool)


def _parse_lines(output: str, tool: str) -> list[Diagnostic]:
    items: list[Diagnostic] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        path = line.split(":", 1)[0]
        items.append(Diagnostic(path=path, message=line, tool=tool))
        if len(items) >= 40:
            break
    return items


def _parse_pyright(output: str, tool: str) -> list[Diagnostic]:
    import json

    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return _parse_lines(output, tool)
    items: list[Diagnostic] = []
    for diag in data.get("generalDiagnostics") or []:
        file = str((diag.get("file") or ""))
        msg = str(diag.get("message") or "")
        items.append(Diagnostic(path=file, message=msg, tool=tool))
    return items
