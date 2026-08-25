# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def run_bash(root: Path, args: dict[str, Any]) -> str:
    command = str(args.get("command") or "").strip()
    if not command:
        return "error: command is required"
    timeout = int(args.get("timeout") or 60)
    try:
        completed = subprocess.run(
            command,
            shell=True,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"error: timed out after {timeout}s"
    output = (completed.stdout or "") + (completed.stderr or "")
    output = output[-12_000:]
    header = f"exit {completed.returncode}"
    return header + ("\n" + output if output.strip() else "")
