# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import sys
from typing import Any


def confirm_bash(_name: str, args: dict[str, Any]) -> bool:
    if os.environ.get("FORGE_YES") == "1":
        return True
    if not sys.stdin.isatty():
        return False
    command = str(args.get("command") or "")
    try:
        reply = input(f"  allow bash `{command}`? [y/N] ").strip().lower()
    except EOFError:
        return False
    return reply in {"y", "yes"}
