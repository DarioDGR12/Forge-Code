# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import os
import sys
from getpass import getpass
from pathlib import Path

from forge_code import __version__
from forge_code.agent import Agent, undo_turn
from forge_code.auth import (
    apply_api_key,
    apply_provider,
    login,
    logout,
    needs_api_key,
    status_rows,
)
from forge_code.commands import load_commands
from forge_code.config import load_config, save_config
from forge_code.diffview import visible_diff
from forge_code.i18n import t
from forge_code.mcp import close_mcp, describe_mcp
from forge_code.models import Message
from forge_code.providers.catalog import DEFAULT_PROVIDERS, aliases_for, is_local, resolve_provider
from forge_code.providers.factory import list_remote_models, probe_local
from forge_code.qa.runner import run_qa
from forge_code.repl import start_repl
from forge_code.scaffold import init_workspace
from forge_code.session import (
    delete_session,
    export_markdown,
    latest_session,
    list_sessions,
    list_shares,
    resolve_session,
    search_sessions,
    share_session,
)
from forge_code.tools.memory import load_memory
from forge_code.tools.registry import default_registry
from forge_code.ui import (
    THEMES,
    auth_table,
    console,
    error,
    info,
    mcp_table,
    ok,
    provider_table,
    qa_panel,
    search_table,
    session_table,
    speak,
)
from forge_code.usage import format_budget
from forge_code.worktree import add_worktree, list_worktrees, remove_worktree


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
    parser.add_argument(
        "-c",
        "--continue",
        dest="continue_last",
        action="store_true",
        help="resume the latest session",
    )
    parser.add_argument("--model", help="model or alias (this invocation)")
    parser.add_argument("--provider", help="provider (this invocation)")
    sub = parser.add_subparsers(dest="cmd")

    run = sub.add_parser("run", help="one-shot non-interactive task", parents=[common])
    run.add_argument("task", help="what to do, or - to read stdin")
    run.add_argument("--json", action="store_true")
    run.add_argument("--plan", action="store_true", help="read-only (no edits)")
    run.add_argument("--quiet", "-q", action="store_true", help="no transcript output")
    run.add_argument("--model", help="model or alias (this invocation)")
    run.add_argument("--provider", help="provider (this invocation)")

    ask = sub.add_parser("ask", help="read-only question (plan mode)", parents=[common])
    ask.add_argument("question", help="what to inspect, or - to read stdin")
    ask.add_argument("--quiet", "-q", action="store_true")
    ask.add_argument("--model", help="model or alias (this invocation)")
    ask.add_argument("--provider", help="provider (this invocation)")

    ci = sub.add_parser("ci", help="non-interactive run for GitHub Actions", parents=[common])
    ci.add_argument("--task", help="task text (or $FORGE_TASK / event)")
    ci.add_argument("--json", action="store_true")
    ci.add_argument("--quiet", "-q", action="store_true")
    ci.add_argument("--model", help="model or alias (this invocation)")
    ci.add_argument("--provider", help="provider (this invocation)")

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
    sub.add_parser("init", help="write AGENTS.md, skills, commands, and ignore", parents=[common])
    sub.add_parser("doctor", help="check providers, local runtimes, and QA", parents=[common])
    sub.add_parser("tools", help="list agent tools")
    sub.add_parser("mcp", help="list configured MCP servers", parents=[common])
    sub.add_parser("diff", help="show last agent edits or git diff", parents=[common])
    sub.add_parser("commands", help="list custom slash commands", parents=[common])
    sub.add_parser("memory", help="print .forge/memory.md", parents=[common])

    worktree = sub.add_parser("worktree", help="isolated git worktrees", parents=[common])
    worktree.add_argument("action", choices=["add", "list", "remove"])
    worktree.add_argument("name", nargs="?", help="worktree name")

    alias_p = sub.add_parser("alias", help="list or set model aliases")
    alias_p.add_argument("action", nargs="?", default="list", choices=["list", "set", "rm"])
    alias_p.add_argument("name", nargs="?")
    alias_p.add_argument("target", nargs="?")

    sub.add_parser("budget", help="show the session token/cost budget")

    share_p = sub.add_parser("share", help="export a session markdown share", parents=[common])
    share_p.add_argument("session_id", nargs="?")
    share_p.add_argument("--out", help="markdown path")

    sub.add_parser("shares", help="list markdown shares", parents=[common])

    theme_p = sub.add_parser("theme", help="set or show the REPL theme")
    theme_p.add_argument("name", nargs="?")

    sessions = sub.add_parser("sessions", help="list or export saved sessions", parents=[common])
    sessions.add_argument(
        "action", nargs="?", default="list", choices=["list", "show", "export", "search", "rm"]
    )
    sessions.add_argument("session_id", nargs="?")
    sessions.add_argument("--out", help="markdown path for export")

    find = sub.add_parser("find", help="search saved sessions", parents=[common])
    find.add_argument("query", nargs="+")

    set_p = sub.add_parser("set", help="set provider, api key, or model")
    set_p.add_argument("what", nargs="?", help="provider | api | model | NAME")
    set_p.add_argument("value", nargs="*", help="value")

    api_p = sub.add_parser("api", help="save the API key for the current provider")
    api_p.add_argument("key", nargs="*", help="API key (prompt if omitted)")

    sub.add_parser("providers", help="list built-in providers")

    args = parser.parse_args(argv)
    root = Path(args.repo).resolve()
    cfg = load_config()
    try:
        _apply_overrides(cfg, args)
    except KeyError as exc:
        error(str(exc))
        return 2

    if args.cmd is None:
        sid = args.resume
        if not sid and getattr(args, "continue_last", False):
            latest = latest_session(root)
            sid = latest.id if latest else None
        return start_repl(root, cfg, session_id=sid)
    if args.cmd == "run":
        task = _maybe_stdin(args.task)
        if not task:
            error("task required (or pass - to read stdin)")
            return 2
        return _cmd_run(root, cfg, task, args.json, plan=args.plan, quiet=args.quiet)
    if args.cmd == "ask":
        question = _maybe_stdin(args.question)
        if not question:
            error("question required (or pass - to read stdin)")
            return 2
        return _cmd_run(root, cfg, question, False, plan=True, quiet=args.quiet)
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
        return _cmd_init(root)
    if args.cmd == "doctor":
        return _cmd_doctor(root, cfg)
    if args.cmd == "tools":
        for name in default_registry().names():
            console.print(f"  {name}")
        return 0
    if args.cmd == "mcp":
        return _cmd_mcp(cfg)
    if args.cmd == "diff":
        diff = visible_diff(root)
        if not diff:
            console.print(t("no_diff"))
            return 0
        console.print(diff, markup=False, highlight=False)
        return 0
    if args.cmd == "commands":
        found = load_commands(root)
        if not found:
            console.print(t("no_commands"))
            return 0
        for item in found.values():
            console.print(f"  /{item.name}  {item.title}")
        return 0
    if args.cmd == "memory":
        text = load_memory(root)
        console.print(text or t("empty_memory"))
        return 0
    if args.cmd == "worktree":
        return _cmd_worktree(root, args)
    if args.cmd == "alias":
        return _cmd_alias(cfg, args)
    if args.cmd == "budget":
        console.print(
            "budget "
            + format_budget(
                cfg.budget.max_usd,
                cfg.budget.max_tokens,
                cfg.budget.max_usd_turn,
                cfg.budget.max_tokens_turn,
            )
        )
        return 0
    if args.cmd == "share":
        return _cmd_share(root, args)
    if args.cmd == "shares":
        return _cmd_shares(root)
    if args.cmd == "theme":
        return _cmd_theme(cfg, args.name)
    if args.cmd == "sessions":
        return _cmd_sessions(root, args)
    if args.cmd == "find":
        return _cmd_find(root, " ".join(args.query))
    if args.cmd == "set":
        return _cmd_set(cfg, args)
    if args.cmd == "api":
        return _cmd_api(cfg, " ".join(args.key))
    if args.cmd == "providers":
        return _cmd_providers(cfg)
    error(f"unknown command {args.cmd}")
    return 2


def _cmd_run(root: Path, cfg, task: str, as_json: bool, plan: bool = False, quiet: bool = False) -> int:
    if plan:
        cfg.mode = "plan"
        cfg.qa.auto = False
    history: list[Message] = []
    try:
        result = Agent(root, cfg).run(history, task)
    except RuntimeError as exc:
        error(str(exc))
        return 2
    finally:
        close_mcp()
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
        if not quiet:
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
    code = _cmd_run(root, cfg, task, args.json, quiet=bool(getattr(args, "quiet", False)))
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
            name = login(args.provider, api_key=args.key, base_url=args.base_url)
        except KeyError as exc:
            error(str(exc))
            return 2
        console.print(f"provider set to [cyan]{name}[/]")
        return 0
    if args.auth_cmd == "logout":
        try:
            logout(args.provider)
        except KeyError as exc:
            error(str(exc))
            return 2
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
    if cfg.aliases:
        console.print("[bold]Aliases[/]")
        for name, target in sorted(cfg.aliases.items()):
            console.print(f"  {name} → {target}")
    return 0


def _cmd_doctor(root: Path, cfg) -> int:
    console.print(f"repo     {root}")
    console.print(f"provider {cfg.provider}")
    console.print(f"model    {cfg.resolved_model()}")
    console.print("aliases  " + (", ".join(f"{k}={v}" for k, v in cfg.aliases.items()) or "(none)"))
    console.print(
        "budget   "
        + format_budget(
            cfg.budget.max_usd,
            cfg.budget.max_tokens,
            cfg.budget.max_usd_turn,
            cfg.budget.max_tokens_turn,
        )
    )
    console.print(f"theme    {cfg.theme}    quiet {'on' if cfg.quiet else 'off'}")
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
    rows = describe_mcp(cfg.mcp)
    if rows:
        mcp_table(rows)
    else:
        console.print("mcp      (none)")
    cmds = load_commands(root)
    console.print("commands " + (", ".join(f"/{n}" for n in cmds) or "(none)"))
    mem = root / ".forge" / "memory.md"
    console.print(f"memory   {'yes' if mem.is_file() else '(empty)'}")
    report = run_qa(root, timeout=cfg.qa.timeout, extra=cfg.qa.extra)
    qa_panel(report)
    save_config(cfg)
    return 0 if report.ok else 1


def _cmd_worktree(root: Path, args: argparse.Namespace) -> int:
    if args.action == "list":
        rows = list_worktrees(root)
        if not rows:
            console.print("no worktrees")
            return 0
        for path, extra in rows:
            console.print(f"  {path}  {extra}")
        return 0
    if not args.name:
        error("worktree name required")
        return 2
    if args.action == "add":
        message = add_worktree(root, args.name)
    else:
        message = remove_worktree(root, args.name)
    if message.startswith("error:"):
        error(message)
        return 2
    ok(message)
    return 0


def _cmd_alias(cfg, args: argparse.Namespace) -> int:
    if args.action == "list":
        if not cfg.aliases:
            console.print("no aliases")
            return 0
        for name, target in sorted(cfg.aliases.items()):
            console.print(f"  {name} → {target}")
        return 0
    if not args.name:
        error("alias name required")
        return 2
    if args.action == "rm":
        if args.name not in cfg.aliases:
            error(f"unknown alias {args.name}")
            return 2
        del cfg.aliases[args.name]
        save_config(cfg)
        ok(f"removed alias {args.name}")
        return 0
    if not args.target:
        error("usage: forge alias set NAME MODEL")
        return 2
    cfg.aliases[args.name] = args.target
    save_config(cfg)
    ok(f"{args.name} → {args.target}")
    return 0


def _cmd_shares(root: Path) -> int:
    rows = list_shares(root)
    if not rows:
        console.print("no shares yet")
        return 0
    for name, dest, size in rows[:30]:
        console.print(f"  {name}  {size}B  {dest}")
    return 0


def _cmd_theme(cfg, name: str | None) -> int:
    if not name:
        console.print(f"theme {cfg.theme}  ({', '.join(THEMES)})")
        return 0
    if name not in THEMES:
        error("theme must be one of: " + ", ".join(THEMES))
        return 2
    cfg.theme = name
    save_config(cfg)
    ok(f"theme → {name}")
    return 0


def _cmd_share(root: Path, args: argparse.Namespace) -> int:
    if args.session_id:
        try:
            session = resolve_session(root, args.session_id)
        except FileNotFoundError as exc:
            error(str(exc))
            return 2
    else:
        items = list_sessions(root)
        if not items:
            error("no sessions to share")
            return 2
        session = items[0]
    dest = Path(args.out) if args.out else None
    path = share_session(root, session, dest)
    ok(t("shared", path=str(path)))
    return 0


def _cmd_init(root: Path) -> int:
    for rel, state in init_workspace(root):
        console.print(f"{state:6} {rel}")
    return 0


def _cmd_mcp(cfg) -> int:
    rows = describe_mcp(cfg.mcp)
    if not rows:
        console.print("no MCP servers in config")
        return 0
    mcp_table(rows)
    return 0


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
    if args.action == "search":
        if not args.session_id:
            error("search query required")
            return 2
        return _cmd_find(root, args.session_id)
    if args.action == "rm":
        if not args.session_id:
            error("session id required")
            return 2
        try:
            deleted = delete_session(root, args.session_id)
        except FileNotFoundError as exc:
            error(str(exc))
            return 2
        ok(f"deleted {deleted}")
        return 0
    if not args.session_id:
        error("session id required")
        return 2
    try:
        session = resolve_session(root, args.session_id)
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


def _cmd_set(cfg, args: argparse.Namespace) -> int:
    what = (args.what or "").strip()
    value = " ".join(args.value).strip()
    if not what:
        console.print(f"provider {cfg.provider}  model {cfg.resolved_model()}")
        console.print(t("set_usage"))
        return 0
    kind = what.lower()
    if kind in {"provider", "prov"}:
        if not value:
            return _cmd_providers(cfg)
        return _switch_provider(cfg, value)
    if kind in {"api", "key", "apikey"}:
        return _cmd_api(cfg, value)
    if kind == "model":
        if not value:
            error(t("set_usage"))
            return 2
        cfg.model = value
        save_config(cfg)
        ok(f"model → {cfg.resolved_model()}")
        return 0
    return _switch_provider(cfg, what)


def _switch_provider(cfg, name: str) -> int:
    try:
        provider = apply_provider(cfg, name)
    except KeyError as exc:
        error(str(exc))
        return 2
    ok(t("provider_set", provider=provider, model=cfg.resolved_model()))
    if needs_api_key(cfg, provider):
        info(t("need_api"))
    return 0


def _cmd_api(cfg, key: str) -> int:
    secret = key.strip()
    if not secret:
        secret = getpass("API key: ").strip()
    try:
        name = apply_api_key(cfg, secret)
    except (KeyError, ValueError) as exc:
        error(str(exc))
        return 2
    ok(t("api_saved", provider=name))
    return 0


def _cmd_providers(cfg) -> int:
    rows: list[tuple[str, str, str, str]] = []
    for name, spec in DEFAULT_PROVIDERS.items():
        mark = "*" if name == cfg.provider else ""
        aliases = ", ".join(aliases_for(name)[:3])
        state = "local" if is_local(spec) else spec.get("key_env") or ""
        rows.append((f"{name}{mark}", spec.get("default_model") or "", aliases, state))
    provider_table(rows)
    return 0


def _cmd_find(root: Path, query: str) -> int:
    hits = search_sessions(root, query)
    if not hits:
        console.print(t("no_matches"))
        return 0
    search_table(
        [(hit.session_id, hit.role, hit.title, hit.snippet) for hit in hits]
    )
    return 0


def _apply_overrides(cfg, args: argparse.Namespace) -> None:
    model = getattr(args, "model", None)
    provider = getattr(args, "provider", None)
    if model:
        cfg.model = model
    if provider:
        cfg.provider = resolve_provider(provider)


def _maybe_stdin(value: str) -> str:
    if value != "-":
        return value
    return sys.stdin.read().strip()


if __name__ == "__main__":
    sys.exit(main())
