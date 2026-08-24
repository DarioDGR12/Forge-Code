# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

from forge_code.agent import Agent
from forge_code.config import AppConfig, save_config
from forge_code.models import Message
from forge_code.qa.runner import run_qa
from forge_code.session import new_session, save_session
from forge_code.ui import banner, error, help_text, info, qa_panel, speak, tool_line

AGENTS_TEMPLATE = """# Agent notes

This file is read by Forge at the start of every session.

## Commands

- Tests:
- Lint:
- Dev server:

## Rules

- Keep changes small.
- Do not commit secrets.
"""


def start_repl(root: Path, cfg: AppConfig) -> int:
    session = new_session(root)
    history: list[Message] = []
    banner(cfg, str(root))

    def on_event(kind: str, message: str) -> None:
        if kind == "tool":
            tool_line(message)
        elif kind == "qa":
            info(message.splitlines()[0] if message else "QA")

    agent = Agent(root, cfg, on_event=on_event)
    while True:
        try:
            raw = input("❯ ").strip()
        except (EOFError, KeyboardInterrupt):
            info("\nbye")
            return 0
        if not raw:
            continue
        if raw.startswith("/"):
            code = _slash(raw, root, cfg, history)
            if code == "exit":
                save_session(root, session)
                return 0
            continue
        try:
            result = agent.run(history, raw)
        except RuntimeError as exc:
            error(str(exc))
            continue
        session.messages = history
        save_session(root, session)
        if result.text:
            speak(result.text)
        if result.qa is not None:
            qa_panel(result.qa)
    return 0


def _slash(raw: str, root: Path, cfg: AppConfig, history: list[Message]) -> str:
    parts = raw[1:].split(maxsplit=1)
    cmd = parts[0].lower() if parts else ""
    arg = parts[1].strip() if len(parts) > 1 else ""
    if cmd in {"exit", "quit", "q"}:
        return "exit"
    if cmd == "help":
        speak(help_text())
        return ""
    if cmd == "status":
        info(
            f"repo={root} provider={cfg.provider} model={cfg.resolved_model()} "
            f"mode={cfg.mode} qa={'on' if cfg.qa.auto else 'off'}"
        )
        return ""
    if cmd == "model" and arg:
        cfg.model = arg
        save_config(cfg)
        info(f"model → {arg}")
        return ""
    if cmd == "provider" and arg:
        cfg.provider = arg
        save_config(cfg)
        info(f"provider → {arg}")
        return ""
    if cmd == "mode" and arg in {"build", "plan"}:
        cfg.mode = arg
        save_config(cfg)
        info(f"mode → {arg}")
        return ""
    if cmd == "qa":
        if arg == "on":
            cfg.qa.auto = True
            save_config(cfg)
            info("auto QA on")
            return ""
        if arg == "off":
            cfg.qa.auto = False
            save_config(cfg)
            info("auto QA off")
            return ""
        qa_panel(run_qa(root, timeout=cfg.qa.timeout))
        return ""
    if cmd == "clear":
        history.clear()
        info("conversation cleared")
        return ""
    if cmd == "init":
        path = root / "AGENTS.md"
        if path.exists():
            info("AGENTS.md already exists")
        else:
            path.write_text(AGENTS_TEMPLATE, encoding="utf-8")
            info("wrote AGENTS.md")
        return ""
    error(f"unknown command /{cmd}. try /help")
    return ""
