# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

from forge_code.auth import needs_api_key
from forge_code.config import AppConfig
from forge_code.project import context_path
from forge_code.providers.catalog import is_local
from forge_code.providers.factory import probe_local
from forge_code.tools.terminal import shell_snapshot


def doctor_lines(root: Path, cfg: AppConfig) -> list[str]:
    spec = cfg.provider_spec()
    if is_local(spec):
        key = "local"
    elif needs_api_key(cfg):
        key = "missing"
    else:
        key = "ok"
    local = probe_local()
    ollama = ", ".join(local.get("ollama") or []) or "down"
    llama = ", ".join(local.get("llamacpp") or []) or "down"
    snap = shell_snapshot(root)
    last = snap.get("last_command") or "-"
    if len(last) > 60:
        last = last[:57] + "..."
    return [
        f"repo      {root}",
        f"provider  {cfg.provider} / {cfg.resolved_model()}",
        f"api       {key}",
        f"ollama    {ollama}",
        f"llama.cpp {llama}",
        f"cwd       {snap.get('cwd') or '.'}",
        f"context   {'yes' if context_path(root).is_file() else 'none'}",
        f"last bash {last}",
    ]
