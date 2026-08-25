# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from forge_code import __version__
from forge_code.agent import Agent, undo_turn
from forge_code.auth import login, logout, status_rows
from forge_code.config import load_config, save_config
from forge_code.models import Message
from forge_code.ui import ok
from forge_code.providers.factory import list_remote_models, probe_local
from forge_code.qa.runner import run_qa
from forge_code.repl import AGENTS_TEMPLATE, start_repl
from forge_code.session import export_markdown, list_sessions, load_session
from forge_code.tools.registry import default_registry
from forge_code.ui import auth_table, console, error, qa_panel, session_table, speak


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="forge",
        description="Open-source AI coding agent for the terminal (BYOK + local models + QA).",
    )
    parser.add_argument("--version", action="version", version=f"forge {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", default=".", help="workspace root")
    parser.add_argument("--repo", default=".", help="workspace root")
    parser.add_argument("--resume", help="resume a session id in the REPL")
    sub = parser.add_subparsers(dest="cmd")

    run = sub.add_parser("run", help="one-shot non-interactive task", parents=[common])
    run.add_argument("task", help="what to do")
    run.add_argument("--json", action="store_true")

    ci = sub.add_parser("ci", help="non-interactive run for GitHub Actions", parents=[common])
    ci.add_argument("--task", help="task text (or $FORGE_TASK / event)")
    ci.add_argument("--json", action="store_true")

    sub.add_parser("undo", help="revert the last agent edits", parents=[common])

    auth = sub.add_parser("auth", help="bring your own keys")
    auth_sub = auth.add_subparsers(dest="auth_cmd", required=True)
    login_p = auth_sub.add_parser("login", help="store a provider key")
    login_p.add_argument("provider")
    login_p.add_argument("--key", help="API key (otherwise prompt)")
    login_p.add_argument("--base-url", help="override endpoint (custom / llama.cpp / proxy)")
    logout_p = auth_sub.add_parser("logout")
    logout_p.add_argument("provider")
    auth_sub.add_parser("status")

    sub.add_parser("models", help="list local and remote models")
    sub.add_parser("qa", help="run the integrated QA suite", parents=[common])
    sub.add_parser("init", help="write AGENTS.md", parents=[common])
    sub.add_parser("doctor", help="check providers, local runtimes, and QA", parents=[common])
    sub.add_parser("tools", help="list agent tools")

    sessions = sub.add_parser("sessions", help="list or export saved sessions", parents=[common])
    sessions.add_argument("action", nargs="?", default="list", choices=["list", "show", "export"])
    sessions.add_argument("session_id", nargs="?")
    sessions.add_argument("--out", help="markdown path for export")

    args = parser.parse_args(argv)
    root = Path(args.repo).resolve()
    cfg = load_config()

    if args.cmd is None:
        return start_repl(root, cfg, session_id=args.resume)
    if args.cmd == "run":
        return _cmd_run(root, cfg, args.task, args.json)
    if args.cmd == "ci":
        return _cmd_ci(root, cfg, args)
    if args.cmd == "undo":
        ok(undo_turn(root))
        return 0
    if args.cmd == "auth":
        return _cmd_auth(args)
    if args.cmd == "models":
        return _cmd_models(cfg)
    if args.cmd == "qa":
        report = run_qa(root, timeout=cfg.qa.timeout, extra=cfg.qa.extra)
        qa_panel(report)
        return 0 if report.ok else 1
    if args.cmd == "init":
        path = root / "AGENTS.md"
        if path.exists():
            console.print("AGENTS.md already exists")
            return 0
        path.write_text(AGENTS_TEMPLATE, encoding="utf-8")
        console.print("wrote AGENTS.md")
        return 0
    if args.cmd == "doctor":
        return _cmd_doctor(root, cfg)
    if args.cmd == "tools":
        for name in default_registry().names():
            console.print(f"  {name}")
        return 0
    if args.cmd == "sessions":
        return _cmd_sessions(root, args)
    error(f"unknown command {args.cmd}")
    return 2


def _cmd_run(root: Path, cfg, task: str, as_json: bool) -> int:
    history: list[Message] = []
    try:
        result = Agent(root, cfg).run(history, task)
    except RuntimeError as exc:
        error(str(exc))
        return 2
    if as_json:
        print(
            json.dumps(
                {
                    "text": result.text,
                    "writes": result.writes,
                    "steps": result.steps,
                    "usage": result.usage.to_dict(),
                    "qa": result.qa.to_dict() if result.qa else None,
                },
                indent=2,
            )
        )
    else:
        if result.text:
            speak(result.text)
        if result.qa is not None:
            qa_panel(result.qa)
    if result.interrupted:
        return 130
    return 0 if (result.qa is None or result.qa.ok) else 1


def _cmd_ci(root: Path, cfg, args: argparse.Namespace) -> int:
    os.environ.setdefault("FORGE_YES", "1")
    task = args.task or os.environ.get("FORGE_TASK") or _task_from_github()
    if task.lower().startswith("/forge "):
        task = task[7:].strip()
    if not task:
        error("ci needs --task or FORGE_TASK")
        return 2
    code = _cmd_run(root, cfg, task, args.json)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        Path(summary).write_text(
            f"## Forge CI\n\nTask: `{task}`\n\nExit: `{code}`\n",
            encoding="utf-8",
        )
    return code


def _task_from_github() -> str:
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not Path(path).is_file():
        return ""
    try:
        event = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    comment = ((event.get("comment") or {}).get("body") or "").strip()
    if comment.lower().startswith("/forge "):
        return comment[7:].strip()
    return str((event.get("inputs") or {}).get("task") or "")


def _cmd_auth(args: argparse.Namespace) -> int:
    if args.auth_cmd == "login":
        try:
            login(args.provider, api_key=args.key, base_url=args.base_url)
        except KeyError as exc:
            error(str(exc))
            return 2
        console.print(f"provider set to [cyan]{args.provider}[/]")
        return 0
    if args.auth_cmd == "logout":
        logout(args.provider)
        console.print(f"removed key for {args.provider}")
        return 0
    auth_table(status_rows())
    return 0


def _cmd_models(cfg) -> int:
    local = probe_local()
    console.print("[bold]Local runtimes[/]")
    console.print(f"  ollama    {', '.join(local['ollama']) or '(offline)'}")
    console.print(f"  llama.cpp {', '.join(local['llamacpp']) or '(offline)'}")
    remote = list_remote_models(cfg)
    if remote:
        console.print(f"[bold]{cfg.provider}[/]")
        for name in remote[:40]:
            console.print(f"  {name}")
    return 0


def _cmd_doctor(root: Path, cfg) -> int:
    console.print(f"repo     {root}")
    console.print(f"provider {cfg.provider}")
    console.print(f"model    {cfg.resolved_model()}")
    console.print(f"mode     {cfg.mode}")
    console.print(f"qa auto  {cfg.qa.auto}")
    console.print(f"bash     {cfg.permissions.bash}")
    auth_table(status_rows())
    local = probe_local()
    console.print(
        f"ollama    {'up: ' + ', '.join(local['ollama']) if local['ollama'] else 'down'}"
    )
    console.print(
        f"llama.cpp {'up: ' + ', '.join(local['llamacpp']) if local['llamacpp'] else 'down'}"
    )
    console.print("tools    " + ", ".join(default_registry().names()))
    report = run_qa(root, timeout=cfg.qa.timeout, extra=cfg.qa.extra)
    qa_panel(report)
    save_config(cfg)
    return 0 if report.ok else 1


def _cmd_sessions(root: Path, args: argparse.Namespace) -> int:
    if args.action == "list":
        rows = [
            (
                item.id,
                (item.updated_at or item.created_at)[:19],
                f"{item.provider}/{item.model}",
                item.title or "(untitled)",
            )
            for item in list_sessions(root)[:30]
        ]
        if not rows:
            console.print("no sessions yet")
            return 0
        session_table(rows)
        return 0
    if not args.session_id:
        error("session id required")
        return 2
    try:
        session = load_session(root, args.session_id)
    except FileNotFoundError as exc:
        error(str(exc))
        return 2
    if args.action == "show":
        console.print(export_markdown(session))
        return 0
    path = Path(args.out) if args.out else Path(f"forge-session-{session.id}.md")
    path.write_text(export_markdown(session), encoding="utf-8")
    console.print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
