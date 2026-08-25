# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from pathlib import Path


def config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    path = base / "forge-code"
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_dir() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    path = base / "forge-code"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sessions_dir(repo: Path) -> Path:
    path = data_dir() / "sessions" / _slug(repo)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _slug(repo: Path) -> str:
    return str(repo.resolve()).replace("/", "_").replace("\\", "_").lstrip("_")
