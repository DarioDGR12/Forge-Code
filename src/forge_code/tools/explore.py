# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any

from forge_code.config import AppConfig


def explore_repo(root: Path, args: dict[str, Any]) -> str:
    """Read-only nested pass: glob + grep + read, no writes."""
    question = str(args.get("question") or "").strip()
    if not question:
        return "error: question is required"

    def live_complete(complete_cfg, messages, tools, **kwargs):
        from forge_code.config import load_config
        from forge_code.providers.factory import complete

        live = load_config()
        live.mode = "plan"
        live.stream = False
        return complete(live, messages, tools)

    try:
        return explore_with_complete(root, question, live_complete)
    except Exception as exc:  # noqa: BLE001
        return f"error: explore failed: {exc}"


def explore_with_complete(root: Path, question: str, complete_fn) -> str:
    from forge_code.agent import Agent
    from forge_code.permissions import PermissionGate
    from forge_code.tools.registry import default_registry

    cfg = AppConfig(provider="openai", model="local", mode="plan", stream=False)
    cfg.qa.auto = False
    registry = default_registry(PermissionGate(root))
    registry.remove("explore")
    agent = Agent(
        root,
        cfg,
        registry=registry,
        max_steps=6,
        complete_fn=complete_fn,
        attach_mcp=False,
    )
    result = agent.run([], f"Explore only. Do not edit. Answer:\n{question}")
    return result.text or "(no answer)"
