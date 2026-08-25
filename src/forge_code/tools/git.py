# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def git_status(root: Path, _args: dict[str, Any]) -> str:
    return _run(root, ["status", "--short", "--branch"])


def git_diff(root: Path, args: dict[str, Any]) -> str:
    command = ["diff"]
    if args.get("staged"):
        command.append("--staged")
    path = str(args.get("path") or "").strip()
    if path:
        command.extend(["--", path])
    return _run(root, command)


def git_log(root: Path, args: dict[str, Any]) -> str:
    count = int(args.get("count") or 8)
    return _run(root, ["log", f"-{max(1, min(count, 30))}", "--oneline"])


def _run(root: Path, args: list[str]) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except FileNotFoundError:
        return "error: git is not installed"
    except subprocess.TimeoutExpired:
        return "error: git timed out"
    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0 and not output.strip():
        return f"error: git exited {completed.returncode}"
    return output.strip() or "(clean)"
