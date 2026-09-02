# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

from forge_code import __version__
from forge_code.auth import needs_api_key
from forge_code.config import AppConfig
from forge_code.files import load_last
from forge_code.journal import journal_path, last_entry
from forge_code.project import context_path
from forge_code.providers.catalog import is_local
from forge_code.providers.factory import probe_local
from forge_code.qa.runner import load_last_qa
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
    qa = load_last_qa(root)
    if qa is None:
        qa_label = "none"
    else:
        qa_label = "pass" if qa.ok else "fail"
    rels = load_last(root)
    turn = last_entry(root)
    turn_line = ""
    if turn:
        body = [ln for ln in turn.splitlines() if ln and not ln.startswith("### ")]
        turn_line = (body[0] if body else turn.splitlines()[0])[:80]
    return [
        f"forge     {__version__}",
        f"repo      {root}",
        f"provider  {cfg.provider} / {cfg.resolved_model()}",
        f"api       {key}",
        f"ollama    {ollama}",
        f"llama.cpp {llama}",
        f"cwd       {snap.get('cwd') or '.'}",
        f"context   {'yes' if context_path(root).is_file() else 'none'}",
        f"files     {', '.join(rels) if rels else 'none'}",
        f"journal   {'yes' if journal_path(root).is_file() else 'none'}",
        f"last-qa   {qa_label}",
        f"last turn {turn_line or 'none'}",
        f"last bash {last}",
    ]
