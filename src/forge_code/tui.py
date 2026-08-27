# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

"""Interactive home screen shown when you run `forge` in a terminal."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

from rich.panel import Panel
from rich.text import Text

from forge_code import __version__
from forge_code.auth import apply_api_key, apply_provider, needs_api_key
from forge_code.config import AppConfig, apply_lang, save_config
from forge_code.i18n import cycle_lang, set_config_lang, t
from forge_code.providers.catalog import DEFAULT_PROVIDERS, aliases_for, is_local
from forge_code.repl import start_repl
from forge_code.session import list_sessions
from forge_code.ui import THEMES, console

BRAND = "O P E N   F O R G E"
WINDOW = 12

Chooser = Callable[[str, list[str], str], int | None]
Asker = Callable[[str], str]
ChatFn = Callable[..., int]


def start_menu(
    root: Path,
    cfg: AppConfig,
    *,
    choose: Chooser | None = None,
    ask: Asker | None = None,
    chat: ChatFn | None = None,
    open_url=None,
) -> int:
    chooser = choose or choose_index
    asker = ask or ask_line
    chatter = chat or start_repl
    set_config_lang(cfg.lang)
    while True:
        extra = _status_line(cfg)
        items = [
            ("providers", t("menu_providers")),
            ("chats", t("menu_chats")),
            ("models", t("menu_models")),
            ("config", t("menu_config")),
            ("contributions", t("menu_contributions")),
            ("help", t("menu_help")),
            ("chat", t("menu_forge")),
            ("quit", t("menu_quit")),
        ]
        picked = _pick(chooser, t("menu_home"), items, extra)
        if picked in (None, "quit"):
            return 0
        if picked == "providers":
            if _providers(cfg, chooser, asker):
                chatter(root, cfg)
            continue
        if picked == "chats":
            sid = _chats(root, chooser)
            if sid is not None:
                chatter(root, cfg, session_id=sid or None)
            continue
        if picked == "models":
            _models(cfg, chooser, asker)
            continue
        if picked == "config":
            _config(cfg, chooser)
            continue
        if picked == "contributions":
            _contributions(chooser, asker, open_url=open_url)
            continue
        if picked == "help":
            _help(cfg, chooser)
            continue
        if picked == "chat":
            if needs_api_key(cfg) and not _providers(cfg, chooser, asker):
                continue
            chatter(root, cfg)
    return 0


def choose_index(title: str, options: list[str], extra: str = "") -> int | None:
    if not options:
        return None
    if sys.stdin.isatty() and sys.stdout.isatty():
        return _choose_arrows(title, options, extra)
    return _choose_numbered(title, options, extra)


def ask_line(prompt: str) -> str:
    console.print(f"[bold]{prompt}[/]")
    try:
        return input("  ").strip()
    except EOFError:
        return ""


def _pick(
    chooser: Chooser, title: str, items: list[tuple[str, str]], extra: str = ""
) -> str | None:
    idx = chooser(title, [label for _key, label in items], extra)
    if idx is None or idx < 0 or idx >= len(items):
        return None
    return items[idx][0]


def _providers(cfg: AppConfig, chooser: Chooser, asker: Asker) -> bool:
    items: list[tuple[str, str]] = []
    for name, spec in DEFAULT_PROVIDERS.items():
        mark = "*" if name == cfg.provider else " "
        also = ", ".join(aliases_for(name)[:2])
        suffix = f"  ({also})" if also else ""
        kind = "local" if is_local(spec) else spec.get("default_model") or ""
        items.append((name, f"{mark} {name}  {kind}{suffix}"))
    items.append(("back", t("menu_back")))
    picked = _pick(chooser, t("menu_providers"), items, _status_line(cfg))
    if picked in (None, "back"):
        return False
    apply_provider(cfg, picked)
    if not needs_api_key(cfg, picked):
        console.print(t("provider_set", provider=cfg.provider, model=cfg.resolved_model()))
        return True
    key = asker(t("menu_api", provider=cfg.provider))
    if not key:
        return False
    apply_api_key(cfg, key, picked)
    console.print(t("api_saved", provider=cfg.provider))
    return True


def _chats(root: Path, chooser: Chooser) -> str | None:
    items = [("new", t("menu_new_chat"))]
    for session in list_sessions(root)[:20]:
        title = session.title or "(untitled)"
        items.append((session.id, f"{session.id}  {title}"))
    items.append(("back", t("menu_back")))
    picked = _pick(chooser, t("menu_chats"), items)
    if picked in (None, "back"):
        return None
    if picked == "new":
        return ""
    return picked


def _models(cfg: AppConfig, chooser: Chooser, asker: Asker) -> None:
    items = [(name, f"{name} → {target}") for name, target in sorted(cfg.aliases.items())]
    items.append(("custom", t("menu_type_model")))
    items.append(("back", t("menu_back")))
    picked = _pick(chooser, t("menu_models"), items, _status_line(cfg))
    if picked in (None, "back"):
        return
    if picked == "custom":
        value = asker(t("menu_type_model"))
        if not value:
            return
        cfg.model = value
    else:
        cfg.model = picked
    save_config(cfg)
    console.print(t("provider_set", provider=cfg.provider, model=cfg.resolved_model()))


def _config(cfg: AppConfig, chooser: Chooser) -> None:
    while True:
        items = [
            ("qa", f"qa  {'on' if cfg.qa.auto else 'off'}"),
            ("bash", f"bash  {cfg.permissions.bash}"),
            ("theme", f"theme  {cfg.theme}"),
            ("quiet", f"quiet  {'on' if cfg.quiet else 'off'}"),
            ("lang", f"{t('help_language')}  {cfg.lang}"),
            ("back", t("menu_back")),
        ]
        picked = _pick(chooser, t("menu_config"), items, _status_line(cfg))
        if picked in (None, "back"):
            return
        if picked == "qa":
            cfg.qa.auto = not cfg.qa.auto
        elif picked == "quiet":
            cfg.quiet = not cfg.quiet
        elif picked == "bash":
            cycle = {"allow": "ask", "ask": "deny", "deny": "allow"}
            cfg.permissions.bash = cycle.get(cfg.permissions.bash, "allow")
        elif picked == "theme":
            idx = THEMES.index(cfg.theme) if cfg.theme in THEMES else 0
            cfg.theme = THEMES[(idx + 1) % len(THEMES)]
        elif picked == "lang":
            apply_lang(cfg, cycle_lang(cfg.lang))
            continue
        save_config(cfg)


def _contributions(chooser: Chooser, asker: Asker, *, open_url=None) -> None:
    import webbrowser

    from forge_code.contribute import (
        FEEDBACK_EMAIL,
        contribute_guide,
        open_github,
        send_recommendation,
    )

    opener = open_url or webbrowser.open
    while True:
        items = [
            ("recommend", t("contrib_recommend")),
            ("code", t("contrib_code")),
            ("back", t("menu_back")),
        ]
        picked = _pick(chooser, t("contrib_title"), items)
        if picked in (None, "back"):
            return
        if picked == "recommend":
            name = (asker(t("contrib_name_prompt")) or "").strip() or "anonymous"
            console.print(t("contrib_body_hint", email=FEEDBACK_EMAIL))
            body = (asker(t("contrib_body_prompt")) or "").strip()
            if not body:
                console.print(t("contrib_empty"))
                continue
            saved, opened = send_recommendation(body, name, open_url=opener)
            console.print(t("contrib_saved", path=str(saved)))
            key = "contrib_mailto_opened" if opened else "contrib_mailto_failed"
            console.print(t(key, email=FEEDBACK_EMAIL))
            continue
        if picked == "code":
            console.print(contribute_guide())
            console.print(t("contrib_opening_github"))
            open_github(open_url=opener)


def _help(cfg: AppConfig, chooser: Chooser) -> None:
    from forge_code.contribute import FEEDBACK_EMAIL, GITHUB_REPO
    from forge_code.ui import help_text

    while True:
        items = [
            ("about", t("help_about")),
            ("commands", t("help_commands")),
            ("lang", f"{t('help_language')}  {cfg.lang}"),
            ("back", t("menu_back")),
        ]
        picked = _pick(chooser, t("help_title"), items, _status_line(cfg))
        if picked in (None, "back"):
            return
        if picked == "about":
            console.print(f"Forge v{__version__}  Apache 2.0")
            console.print(t("help_about_body"))
            console.print(GITHUB_REPO)
            console.print(FEEDBACK_EMAIL)
            continue
        if picked == "commands":
            console.print(help_text())
            continue
        if picked == "lang":
            apply_lang(cfg, cycle_lang(cfg.lang))


def _status_line(cfg: AppConfig) -> str:
    key = "local" if not needs_api_key(cfg) else t("menu_need_key")
    return f"{cfg.provider} / {cfg.resolved_model()}    {key}"


def _draw(title: str, options: list[str], index: int, extra: str, numbered: bool) -> None:
    theme = "cyan"
    start = 0
    if index >= WINDOW:
        start = index - WINDOW + 1
    view = options[start : start + WINDOW]
    lines: list[str] = []
    if extra:
        lines.append(f"[dim]{extra}[/]")
        lines.append("")
    for i, label in enumerate(view):
        real = start + i
        cursor = "›" if real == index and not numbered else " "
        num = f"{real + 1:>2}  " if numbered else ""
        if real == index:
            lines.append(f"[bold {theme}]{cursor} {num}{label}[/]")
        else:
            lines.append(f"  {num}{label}")
    if start > 0 or start + WINDOW < len(options):
        lines.append("")
        lines.append(f"[dim]{start + 1}–{min(len(options), start + WINDOW)} / {len(options)}[/]")
    lines.append("")
    lines.append(f"[dim]{t('menu_hint')}[/]")
    body = Text.from_markup("\n".join(lines))
    header = f"{BRAND}  v{__version__}"
    console.print(Panel(body, title=header, subtitle=title, border_style=theme, padding=(1, 3)))


def _choose_numbered(title: str, options: list[str], extra: str) -> int | None:
    _draw(title, options, 0, extra, numbered=True)
    try:
        raw = input("› ").strip().lower()
    except EOFError:
        return None
    if raw in {"", "q", "quit"}:
        return None
    if raw.isdigit():
        n = int(raw)
        if 1 <= n <= len(options):
            return n - 1
    return None


def _choose_arrows(title: str, options: list[str], extra: str) -> int | None:
    idx = 0
    while True:
        console.clear()
        _draw(title, options, idx, extra, numbered=False)
        key = _read_key()
        if key == "up":
            idx = (idx - 1) % len(options)
        elif key == "down":
            idx = (idx + 1) % len(options)
        elif key == "enter":
            return idx
        elif key in {"quit", "esc"}:
            return None


def _read_key() -> str:
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            rest = sys.stdin.read(2)
            if rest == "[A":
                return "up"
            if rest == "[B":
                return "down"
            return "esc"
        if ch in {"\r", "\n"}:
            return "enter"
        if ch in {"q", "Q", "\x03"}:
            return "quit"
        if ch == "k":
            return "up"
        if ch == "j":
            return "down"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
