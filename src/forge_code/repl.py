# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from pathlib import Path

from forge_code.agent import Agent, undo_turn
from forge_code.auth import apply_api_key, apply_provider, needs_api_key
from forge_code.commands import expand_command, load_commands
from forge_code.compact import compact_messages
from forge_code.config import AppConfig, apply_lang, save_config
from forge_code.diffview import visible_diff
from forge_code.i18n import t
from forge_code.interrupt import CancelFlag
from forge_code.mcp import close_mcp, describe_mcp
from forge_code.models import Message
from forge_code.qa.runner import run_qa
from forge_code.providers.catalog import DEFAULT_PROVIDERS, aliases_for, is_local
from forge_code.scaffold import init_workspace
from forge_code.session import (
    delete_session,
    export_markdown,
    list_sessions,
    list_shares,
    new_session,
    resolve_session,
    save_session,
    search_sessions,
    share_session,
)
from forge_code.tools.memory import load_memory, memory_write
from forge_code.tools.registry import default_registry
from forge_code.ui import (
    THEMES,
    banner,
    console,
    error,
    files_panel,
    help_text,
    info,
    ok,
    provider_table,
    qa_panel,
    search_table,
    session_table,
    show_copyable,
    speak,
    tool_line,
    tool_result,
    usage_line,
)
from forge_code.usage import Usage, budget_hit, format_budget, format_remaining, format_usage

HISTORY_PATH_ENV = "FORGE_HISTORY"
RUN_PREFIX = ">>"
REVIEW_PROMPT = (
    "Review the working tree. Use git_status and git_diff. "
    "List bugs, risks, and missing tests. Do not edit."
)


def start_repl(root: Path, cfg: AppConfig, session_id: str | None = None) -> int:
    _enable_readline(root)
    if session_id:
        try:
            session = resolve_session(root, session_id)
        except FileNotFoundError as exc:
            error(str(exc))
            return 2
        history = list(session.messages)
        info(f"resumed session {session.id}")
    else:
        session = new_session(root, provider=cfg.provider, model=cfg.resolved_model())
        history: list[Message] = []
    banner(cfg, str(root), session.id)
    totals = session.usage or Usage()

    def on_event(kind: str, message: str) -> None:
        if kind == "stream":
            console.print(message, end="", highlight=False)
        elif kind == "stream_end":
            console.print()
        elif kind == "tool":
            tool_line(message)
        elif kind == "tool_result":
            if not cfg.quiet:
                tool_result(message)
        elif kind == "qa":
            info(message.splitlines()[0] if message else "QA")
        elif kind == "lsp":
            info(message.splitlines()[0] if message else "LSP")
        elif kind == "diff":
            info(message.splitlines()[0] if message else "diff")
        elif kind == "hook":
            info(message.splitlines()[0] if message else "hook")
        elif kind == "compact":
            info(message)
        elif kind == "budget":
            info(message)
        elif kind == "assistant":
            speak(message)

    cancel = CancelFlag()
    agent = Agent(root, cfg, on_event=on_event, cancel=cancel, session_usage=totals)
    while True:
        try:
            raw = _read_input()
        except (EOFError, KeyboardInterrupt):
            info("\n" + t("bye"))
            save_session(root, session)
            close_mcp()
            return 0
        if not raw:
            continue
        if raw.startswith("/"):
            code = _slash(raw, root, cfg, history, session, totals)
            if code == "exit":
                save_session(root, session)
                close_mcp()
                return 0
            if code.startswith(RUN_PREFIX):
                raw = code[len(RUN_PREFIX) :]
            else:
                continue
        reason = budget_hit(
            cfg.resolved_model(), totals, cfg.budget.max_usd, cfg.budget.max_tokens
        )
        if reason:
            error(t("budget_hit") + f" ({reason})")
            continue
        cancel.reset()
        try:
            result = agent.run(history, raw)
        except KeyboardInterrupt:
            cancel.cancel()
            info(t("interrupted"))
            continue
        except RuntimeError as exc:
            error(str(exc))
            continue
        totals = totals.add(result.usage)
        agent.session_usage = totals
        session.messages = history
        session.usage = totals
        session.touch(title=raw)
        session.provider = cfg.provider
        session.model = cfg.resolved_model()
        save_session(root, session)
        if result.interrupted:
            info(t("interrupted"))
        if result.budget_hit:
            info(t("budget_hit"))
        if result.qa is not None:
            qa_panel(result.qa)
        if result.writes:
            from forge_code.files import files_dir, save_turn

            rels = save_turn(root, result.writes) or [p for p in result.writes if p]
            files_panel(rels, str(files_dir(root)))
            if not cfg.quiet:
                show_copyable(root, rels)
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
        "/providers",
        "/set provider ",
        "/set lang ",
        "/api ",
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
        "/undo",
        "/diff",
        "/review",
        "/ask ",
        "/retry",
        "/last",
        "/find ",
        "/pin",
        "/new",
        "/rename ",
        "/copy",
        "/files",
        "/commands",
        "/memory",
        "/context",
        "/terminal",
        "/alias ",
        "/budget",
        "/share",
        "/shares",
        "/theme ",
        "/quiet",
        "/mcp",
        "/bash allow",
        "/bash ask",
        "/bash deny",
        "/exit",
    ]

    commands.extend(f"/{name}" for name in load_commands(root))

    def completer(text: str, state: int) -> str | None:
        opts = [item for item in commands if item.startswith(text)]
        if state < len(opts):
            return opts[state]
        return None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")


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
        left = format_remaining(
            cfg.resolved_model(), totals, cfg.budget.max_usd, cfg.budget.max_tokens
        )
        info(
            f"repo={root} session={session.id} provider={cfg.provider} "
            f"model={cfg.resolved_model()} mode={cfg.mode} qa={'on' if cfg.qa.auto else 'off'} "
            f"theme={cfg.theme} quiet={'on' if cfg.quiet else 'off'}"
            + (f" · {left}" if left else "")
        )
        return ""
    if cmd == "tools":
        info(" ".join(default_registry().names()))
        return ""
    if cmd == "model":
        if not arg:
            info(f"model {cfg.model or '(default)'} → {cfg.resolved_model()}")
            for name, target in sorted(cfg.aliases.items()):
                info(f"  {name} = {target}")
            return ""
        cfg.model = arg
        save_config(cfg)
        resolved = cfg.resolved_model()
        if arg in cfg.aliases and cfg.aliases[arg] != arg:
            ok(f"model → {arg} ({resolved})")
        else:
            ok(f"model → {resolved}")
        return ""
    if cmd == "provider":
        if not arg:
            info(f"provider {cfg.provider} → {cfg.resolved_model()}")
            return ""
        return _slash_provider(cfg, arg)
    if cmd == "providers":
        _print_providers(cfg)
        return ""
    if cmd == "set":
        return _slash_set(cfg, arg)
    if cmd == "api":
        return _slash_api(cfg, arg)
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
        compacted = compact_messages(history, hard=arg == "hard")
        history.clear()
        history.extend(compacted)
        session.messages = history
        save_session(root, session)
        ok(f"compacted to {len(history)} messages")
        return ""
    if cmd == "cost":
        info(format_usage(cfg.resolved_model(), totals))
        left = format_remaining(
            cfg.resolved_model(), totals, cfg.budget.max_usd, cfg.budget.max_tokens
        )
        if left:
            info(left)
        return ""
    if cmd == "sessions":
        if arg == "rm" or arg.startswith("rm "):
            sid = arg[2:].strip()
            if not sid:
                error(t("sessions_rm_usage"))
                return ""
            try:
                target = resolve_session(root, sid)
            except FileNotFoundError as exc:
                error(str(exc))
                return ""
            if target.id == session.id:
                error(t("cannot_delete_current"))
                return ""
            delete_session(root, target.id)
            ok(t("deleted", id=target.id))
            return ""
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
    if cmd == "share":
        dest = Path(arg) if arg else None
        path = share_session(root, session, dest)
        ok(t("shared", path=str(path)))
        return ""
    if cmd == "alias":
        return _slash_alias(cfg, arg)
    if cmd == "budget":
        return _slash_budget(cfg, arg)
    if cmd == "theme":
        return _slash_theme(cfg, arg)
    if cmd == "quiet":
        if arg in {"on", "1", "true"}:
            cfg.quiet = True
        elif arg in {"off", "0", "false"}:
            cfg.quiet = False
        else:
            cfg.quiet = not cfg.quiet
        save_config(cfg)
        ok(f"quiet → {'on' if cfg.quiet else 'off'}")
        return ""
    if cmd == "shares":
        rows = list_shares(root)
        if not rows:
            info("no shares yet")
        else:
            for name, dest, size in rows[:20]:
                info(f"{name}  {size}B  {dest}")
        return ""
    if cmd == "undo":
        ok(undo_turn(root))
        return ""
    if cmd == "diff":
        diff = visible_diff(root)
        if not diff:
            info(t("no_diff"))
        else:
            speak(f"```diff\n{diff}\n```")
        return ""
    if cmd == "review":
        cfg.mode = "plan"
        prompt = REVIEW_PROMPT
        if arg:
            prompt += f"\nFocus: {arg}"
        ok("mode → plan (review). /mode build to edit")
        return RUN_PREFIX + prompt
    if cmd == "ask":
        if not arg:
            error(t("ask_usage"))
            return ""
        cfg.mode = "plan"
        ok("mode → plan (ask). /mode build to edit")
        return RUN_PREFIX + arg
    if cmd == "retry":
        if not session.title:
            info(t("nothing_retry"))
            return ""
        return RUN_PREFIX + session.title
    if cmd == "last":
        for message in reversed(history):
            if message.role == "assistant" and message.content.strip():
                speak(message.content)
                return ""
        info(t("no_reply"))
        return ""
    if cmd == "files":
        from forge_code.files import files_dir, load_last

        rels = load_last(root)
        if not rels:
            info(t("empty_files"))
            return ""
        files_panel(rels, str(files_dir(root)))
        show_copyable(root, rels)
        return ""
    if cmd == "copy":
        from forge_code.files import read_for_copy

        path, body = read_for_copy(root, arg or None)
        text = body
        if not text:
            for message in reversed(history):
                if message.role == "assistant" and message.content.strip():
                    text = message.content
                    path = ""
                    break
        if not text:
            info(t("no_reply"))
            return ""
        if _copy_text(text):
            ok(t("copied_file", path=path) if path else t("copied"))
        else:
            speak(f"```\n{text}\n```" if path else text)
            info(t("no_clipboard"))
        return ""
    if cmd == "new":
        save_session(root, session)
        fresh = new_session(root, provider=cfg.provider, model=cfg.resolved_model())
        session.id = fresh.id
        session.created_at = fresh.created_at
        session.updated_at = fresh.updated_at
        session.title = arg[:80] if arg else ""
        session.messages = []
        session.usage = Usage()
        session.provider = cfg.provider
        session.model = cfg.resolved_model()
        if arg:
            save_session(root, session)
        history.clear()
        totals.prompt_tokens = 0
        totals.completion_tokens = 0
        ok(t("new_session", id=session.id))
        return ""
    if cmd == "rename":
        if not arg:
            error(t("rename_usage"))
            return ""
        session.title = arg[:80]
        save_session(root, session)
        ok(t("renamed", title=session.title))
        return ""
    if cmd == "find":
        if not arg:
            error(t("find_usage"))
            return ""
        hits = search_sessions(root, arg)
        if not hits:
            info(t("no_matches"))
        else:
            search_table(
                [(hit.session_id, hit.role, hit.title, hit.snippet) for hit in hits[:20]]
            )
        return ""
    if cmd == "pin":
        note = arg.strip()
        if not note:
            for message in reversed(history):
                if message.role == "assistant" and message.content.strip():
                    note = message.content.strip()
                    break
        if not note:
            info(t("no_reply"))
            return ""
        result = memory_write(root, {"note": note})
        if result.startswith("error:"):
            error(result)
        else:
            ok(t("pinned"))
        return ""
    if cmd == "commands":
        found = load_commands(root)
        if not found:
            info(t("no_commands"))
        else:
            for item in found.values():
                info(f"/{item.name}  {item.title}")
        return ""
    if cmd == "memory":
        text = load_memory(root)
        if not text:
            info(t("empty_memory"))
        else:
            speak(text)
        return ""
    if cmd == "context":
        from forge_code.project import ensure_context, save_context

        if arg in {"refresh", "scan"}:
            save_context(root)
            ok("context refreshed")
        text = ensure_context(root)
        speak(text or "(empty context)")
        return ""
    if cmd == "terminal":
        from forge_code.tools.terminal import load_terminal

        text = load_terminal(root)
        speak(text or "(empty terminal log)")
        return ""
    if cmd == "mcp":
        rows = describe_mcp(cfg.mcp)
        if not rows:
            info("no MCP servers in config")
        else:
            for name, cmdline, state in rows:
                info(f"{name}  {cmdline}  {state}")
        return ""
    if cmd == "bash" and arg in {"allow", "ask", "deny"}:
        cfg.permissions.bash = arg
        save_config(cfg)
        ok(f"bash → {arg}")
        return ""
    if cmd == "clear":
        history.clear()
        ok("conversation cleared")
        return ""
    if cmd == "init":
        for rel, state in init_workspace(root):
            if state == "wrote":
                ok(f"wrote {rel}")
            else:
                info(f"{rel} already exists")
        return ""
    custom = load_commands(root).get(cmd)
    if custom:
        return RUN_PREFIX + expand_command(custom, arg)
    error(f"unknown command /{cmd}. try /help")
    return ""


def _slash_alias(cfg: AppConfig, arg: str) -> str:
    if not arg:
        if not cfg.aliases:
            info("no aliases")
            return ""
        for name, target in sorted(cfg.aliases.items()):
            info(f"  {name} = {target}")
        return ""
    parts = arg.split(maxsplit=2)
    if parts[0] == "rm" and len(parts) == 2:
        if parts[1] not in cfg.aliases:
            error(f"unknown alias {parts[1]}")
            return ""
        del cfg.aliases[parts[1]]
        save_config(cfg)
        ok(f"removed alias {parts[1]}")
        return ""
    if len(parts) >= 2 and parts[0] != "rm":
        name, target = parts[0], parts[1]
        if not name.replace("-", "").replace("_", "").isalnum():
            error("alias name must be letters, digits, '-' or '_'")
            return ""
        cfg.aliases[name] = target
        save_config(cfg)
        ok(f"{name} → {target}")
        return ""
    error("usage: /alias  |  /alias NAME MODEL  |  /alias rm NAME")
    return ""


def _budget_label(cfg: AppConfig) -> str:
    return format_budget(
        cfg.budget.max_usd,
        cfg.budget.max_tokens,
        cfg.budget.max_usd_turn,
        cfg.budget.max_tokens_turn,
    )


def _slash_budget(cfg: AppConfig, arg: str) -> str:
    if not arg:
        info("budget " + _budget_label(cfg))
        return ""
    if arg in {"off", "0"}:
        cfg.budget.max_usd = 0.0
        cfg.budget.max_tokens = 0
        cfg.budget.max_usd_turn = 0.0
        cfg.budget.max_tokens_turn = 0
        save_config(cfg)
        ok("budget off")
        return ""
    parts = arg.split()
    if parts[0] == "tokens" and len(parts) == 2:
        try:
            cfg.budget.max_tokens = max(0, int(parts[1]))
        except ValueError:
            error("usage: /budget tokens 50000")
            return ""
        save_config(cfg)
        ok("budget " + _budget_label(cfg))
        return ""
    if parts[0] == "turn" and len(parts) == 2:
        try:
            cfg.budget.max_usd_turn = max(0.0, float(parts[1]))
        except ValueError:
            error("usage: /budget turn 0.10")
            return ""
        save_config(cfg)
        ok("budget " + _budget_label(cfg))
        return ""
    if parts[0] in {"turn-tokens", "turn_tokens"} and len(parts) == 2:
        try:
            cfg.budget.max_tokens_turn = max(0, int(parts[1]))
        except ValueError:
            error("usage: /budget turn-tokens 8000")
            return ""
        save_config(cfg)
        ok("budget " + _budget_label(cfg))
        return ""
    try:
        cfg.budget.max_usd = max(0.0, float(parts[0]))
    except ValueError:
        error(
            "usage: /budget  |  /budget 0.25  |  /budget tokens 50000  |  "
            "/budget turn 0.10  |  /budget turn-tokens 8000  |  /budget off"
        )
        return ""
    save_config(cfg)
    ok("budget " + _budget_label(cfg))
    return ""


def _slash_theme(cfg: AppConfig, arg: str) -> str:
    if not arg:
        info("theme " + cfg.theme + "  (" + ", ".join(THEMES) + ")")
        return ""
    if arg not in THEMES:
        error("theme must be one of: " + ", ".join(THEMES))
        return ""
    cfg.theme = arg
    save_config(cfg)
    ok(f"theme → {arg}")
    return ""


def _slash_set(cfg: AppConfig, arg: str) -> str:
    if not arg:
        info(f"provider {cfg.provider} → {cfg.resolved_model()}")
        info(t("set_usage"))
        return ""
    parts = arg.split(maxsplit=1)
    kind = parts[0].lower()
    value = parts[1].strip() if len(parts) > 1 else ""
    if kind in {"provider", "prov"}:
        if not value:
            _print_providers(cfg)
            return ""
        return _slash_provider(cfg, value)
    if kind in {"api", "key", "apikey"}:
        return _slash_api(cfg, value)
    if kind == "model":
        if not value:
            error(t("set_usage"))
            return ""
        cfg.model = value
        save_config(cfg)
        ok(f"model → {cfg.resolved_model()}")
        return ""
    if kind in {"lang", "language"}:
        if not value:
            ok(t("lang_set", lang=cfg.lang))
            return ""
        try:
            apply_lang(cfg, value)
        except ValueError as exc:
            error(str(exc))
            return ""
        ok(t("lang_set", lang=cfg.lang))
        return ""
    return _slash_provider(cfg, arg)


def _slash_provider(cfg: AppConfig, name: str) -> str:
    try:
        provider = apply_provider(cfg, name)
    except KeyError as exc:
        error(str(exc))
        return ""
    ok(t("provider_set", provider=provider, model=cfg.resolved_model()))
    if needs_api_key(cfg, provider):
        info(t("need_api_repl"))
    return ""


def _slash_api(cfg: AppConfig, key: str) -> str:
    if not key.strip():
        error(t("api_usage"))
        return ""
    try:
        name = apply_api_key(cfg, key)
    except (KeyError, ValueError) as exc:
        error(str(exc))
        return ""
    ok(t("api_saved", provider=name))
    return ""


def _print_providers(cfg: AppConfig) -> None:
    rows: list[tuple[str, str, str, str]] = []
    for name, spec in DEFAULT_PROVIDERS.items():
        mark = "*" if name == cfg.provider else ""
        aliases = ", ".join(aliases_for(name)[:3])
        state = "local" if is_local(spec) else spec.get("key_env") or ""
        rows.append((f"{name}{mark}", spec.get("default_model") or "", aliases, state))
    provider_table(rows)


def _copy_text(text: str) -> bool:
    from forge_code.files import copy_to_clipboard

    return copy_to_clipboard(text)
