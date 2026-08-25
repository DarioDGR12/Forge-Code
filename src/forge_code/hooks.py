# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import subprocess
from pathlib import Path

HOOK_NAMES = ("pre_edit", "post_edit", "post_turn")


def run_hook(root: Path, name: str, extra_env: dict[str, str] | None = None) -> str:
    if name not in HOOK_NAMES:
        return f"error: unknown hook {name}"
    path = root / ".forge" / "hooks" / name
    if not path.is_file():
        return ""
    env = os.environ.copy()
    env["FORGE_HOOK"] = name
    env["FORGE_ROOT"] = str(root)
    if extra_env:
        env.update(extra_env)
    command = [str(path)] if os.access(path, os.X_OK) else ["sh", str(path)]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env=env,
        )
    except OSError as exc:
        return f"error: hook {name}: {exc}"
    except subprocess.TimeoutExpired:
        return f"error: hook {name} timed out"
    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        return f"error: hook {name} exited {completed.returncode}\n{output.strip()}"
    return output.strip()
