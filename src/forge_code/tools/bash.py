# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


from forge_code.tools.base import jail
from forge_code.tools.terminal import apply_cd, load_cwd, log_command, save_cwd


def run_bash(root: Path, args: dict[str, Any]) -> str:
    command = str(args.get("command") or "").strip()
    if not command:
        return "error: command is required"
    timeout = int(args.get("timeout") or 60)
    cwd_arg = str(args.get("cwd") or "").strip()
    if cwd_arg:
        try:
            cwd = jail(root, cwd_arg)
        except PermissionError as exc:
            return f"error: {exc}"
        if not cwd.is_dir():
            return f"error: cwd is not a directory: {cwd_arg}"
        save_cwd(root, cwd.relative_to(root.resolve()).as_posix() or ".")
    else:
        cwd = load_cwd(root)
    try:
        completed = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"error: timed out after {timeout}s"
    output = (completed.stdout or "") + (completed.stderr or "")
    output = output[-12_000:]
    cwd_rel = cwd.resolve().relative_to(root.resolve()).as_posix() or "."
    apply_cd(root, cwd, command)
    log_command(root, command, completed.returncode, output, cwd_rel)
    header = f"exit {completed.returncode}"
    return header + ("\n" + output if output.strip() else "")
