# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

from forge_code.auth import needs_api_key
from forge_code.config import AppConfig
from forge_code.providers.catalog import is_local
from forge_code.providers.factory import probe_local


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
    return [
        f"repo      {root}",
        f"provider  {cfg.provider} / {cfg.resolved_model()}",
        f"api       {key}",
        f"ollama    {ollama}",
        f"llama.cpp {llama}",
    ]
