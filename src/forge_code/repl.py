# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from pathlib import Path

from rich.status import Status

from forge_code.agent import Agent
from forge_code.compact import compact_messages
from forge_code.config import AppConfig, save_config
from forge_code.models import Message
from forge_code.qa.runner import run_qa
from forge_code.session import (
    export_markdown,
    list_sessions,
    load_session,
    new_session,
    save_session,
)
from forge_code.tools.registry import default_registry
from forge_code.ui import (
    banner,
    error,
    help_text,
    info,
    ok,
    qa_panel,
    session_table,
    speak,
    tool_line,
    tool_result,
    usage_line,
)
from forge_code.usage import Usage, format_usage

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

HISTORY_PATH_ENV = "FORGE_HISTORY"


def start_repl(root: Path, cfg: AppConfig, session_id: str | None = None) -> int:
    _enable_readline(root)
    if session_id:
        session = load_session(root, session_id)
        history = list(session.messages)
        info(f"resumed session {session.id}")
    else:
        session = new_session(root, provider=cfg.provider, model=cfg.resolved_model())
        history: list[Message] = []
    banner(cfg, str(root), session.id)
    totals = session.usage or Usage()

    def on_event(kind: str, message: str) -> None:
        if kind == "tool":
            tool_line(message)
        elif kind == "tool_result":
            tool_result(message)
        elif kind == "qa":
            info(message.splitlines()[0] if message else "QA")
        elif kind == "compact":
            info(message)

    agent = Agent(root, cfg, on_event=on_event)
    while True:
        try:
            raw = _read_input()
        except (EOFError, KeyboardInterrupt):
            info("\nbye")
            save_session(root, session)
            return 0
        if not raw:
            continue
        if raw.startswith("/"):
            code = _slash(raw, root, cfg, history, session, totals)
            if code == "exit":
                save_session(root, session)
                return 0
            continue
        try:
            with Status("[cyan]forging…[/]", spinner="dots"):
                result = agent.run(history, raw)
        except RuntimeError as exc:
            error(str(exc))
            continue
        totals = totals.add(result.usage)
        session.messages = history
        session.usage = totals
        session.touch(title=raw)
        session.provider = cfg.provider
        session.model = cfg.resolved_model()
        save_session(root, session)
        if result.text:
            speak(result.text)
        if result.qa is not None:
            qa_panel(result.qa)
        usage_line(cfg.resolved_model(), result.usage)
    return 0


def _read_input() -> str:
    first = input("❯ ").rstrip()
    if first.endswith("\\"):
        chunks = [first[:-1]]
        while True:
            nxt = input("· ").rstrip()
            if not nxt.endswith("\\"):
                chunks.append(nxt)
                break
            chunks.append(nxt[:-1])
        return "\n".join(chunks).strip()
    return first.strip()


def _enable_readline(root: Path) -> None:
    try:
        import readline
    except ImportError:
        return
    hist = Path(os.environ.get(HISTORY_PATH_ENV) or (Path.home() / ".forge_history"))
    try:
        if hist.exists():
            readline.read_history_file(hist)
        readline.set_history_length(1000)
    except OSError:
        pass

    def _save() -> None:
        try:
            readline.write_history_file(hist)
        except OSError:
            pass

    import atexit

    atexit.register(_save)
    commands = [
        "/help",
        "/status",
        "/tools",
        "/model ",
        "/provider ",
        "/mode build",
        "/mode plan",
        "/qa",
        "/compact",
        "/cost",
        "/sessions",
        "/resume ",
        "/export",
        "/init",
        "/clear",
        "/exit",
    ]

    def completer(text: str, state: int) -> str | None:
        opts = [item for item in commands if item.startswith(text)]
        if state < len(opts):
            return opts[state]
        return None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    del root


def _slash(
    raw: str,
    root: Path,
    cfg: AppConfig,
    history: list[Message],
    session,
    totals: Usage,
) -> str:
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
            f"repo={root} session={session.id} provider={cfg.provider} "
            f"model={cfg.resolved_model()} mode={cfg.mode} qa={'on' if cfg.qa.auto else 'off'}"
        )
        return ""
    if cmd == "tools":
        info(" ".join(default_registry().names()))
        return ""
    if cmd == "model" and arg:
        cfg.model = arg
        save_config(cfg)
        ok(f"model → {arg}")
        return ""
    if cmd == "provider" and arg:
        cfg.provider = arg
        save_config(cfg)
        ok(f"provider → {arg}")
        return ""
    if cmd == "mode" and arg in {"build", "plan"}:
        cfg.mode = arg
        save_config(cfg)
        ok(f"mode → {arg}")
        return ""
    if cmd == "qa":
        if arg == "on":
            cfg.qa.auto = True
            save_config(cfg)
            ok("auto QA on")
            return ""
        if arg == "off":
            cfg.qa.auto = False
            save_config(cfg)
            ok("auto QA off")
            return ""
        qa_panel(run_qa(root, timeout=cfg.qa.timeout, extra=cfg.qa.extra))
        return ""
    if cmd == "compact":
        compacted = compact_messages(history)
        history.clear()
        history.extend(compacted)
        session.messages = history
        save_session(root, session)
        ok(f"compacted to {len(history)} messages")
        return ""
    if cmd == "cost":
        info(format_usage(cfg.resolved_model(), totals))
        return ""
    if cmd == "sessions":
        rows = [
            (
                item.id,
                (item.updated_at or item.created_at)[:19],
                f"{item.provider}/{item.model}",
                item.title or "(untitled)",
            )
            for item in list_sessions(root)[:15]
        ]
        session_table(rows)
        return ""
    if cmd == "resume" and arg:
        error("restart with: forge --resume " + arg)
        return ""
    if cmd == "export":
        path = Path(arg) if arg else Path(f"forge-session-{session.id}.md")
        path.write_text(export_markdown(session), encoding="utf-8")
        ok(f"wrote {path}")
        return ""
    if cmd == "clear":
        history.clear()
        ok("conversation cleared")
        return ""
    if cmd == "init":
        path = root / "AGENTS.md"
        if path.exists():
            info("AGENTS.md already exists")
        else:
            path.write_text(AGENTS_TEMPLATE, encoding="utf-8")
            ok("wrote AGENTS.md")
        return ""
    error(f"unknown command /{cmd}. try /help")
    return ""
