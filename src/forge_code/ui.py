# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from forge_code import __version__
from forge_code.config import AppConfig
from forge_code.qa.runner import QAReport
from forge_code.usage import Usage, format_usage

console = Console()

THEMES = (
    "cyan",
    "magenta",
    "green",
    "blue",
    "yellow",
    "red",
    "white",
    "bright_cyan",
)


def banner(cfg: AppConfig, repo: str, session_id: str = "") -> None:
    theme = cfg.theme or "cyan"
    title = Text.assemble(("Forge", f"bold {theme}"), ("  ", "dim"), (f"v{__version__}", "dim"))
    session_line = f"[dim]session[/] {session_id}\n" if session_id else ""
    body = (
        f"{session_line}"
        f"[dim]repo[/]     {repo}\n"
        f"[dim]model[/]    {cfg.provider}/{cfg.resolved_model()}\n"
        f"[dim]mode[/]     {cfg.mode}    [dim]qa[/] {'on' if cfg.qa.auto else 'off'}    "
        f"[dim]bash[/] {cfg.permissions.bash}"
        f"{'    [dim]quiet[/] on' if cfg.quiet else ''}\n\n"
        "[dim]Type a task, or /help. Not affiliated with OpenCode or Anthropic.[/]"
    )
    console.print(Panel(body, title=title, border_style=theme, padding=(1, 2)))


def speak(text: str) -> None:
    if not text.strip():
        return
    console.print()
    console.print(Markdown(text))
    console.print()


def tool_line(message: str) -> None:
    console.print(f"  [cyan]▸[/] [white]{message}[/]")


def tool_result(message: str) -> None:
    snippet = message.strip().splitlines()
    if not snippet:
        return
    preview = snippet[0][:120]
    extra = f"  [dim](+{len(snippet) - 1} lines)[/]" if len(snippet) > 1 else ""
    console.print(f"    [dim]{preview}[/]{extra}")


def qa_panel(report: QAReport) -> None:
    style = "green" if report.ok else "red"
    console.print(Panel(report.summary(), title="QA", border_style=style))


def usage_line(model: str, usage: Usage) -> None:
    if usage.total <= 0:
        return
    console.print(f"  [dim]{format_usage(model, usage)}[/]")


def error(message: str) -> None:
    console.print(f"[red]error[/] {message}")


def info(message: str) -> None:
    console.print(f"[dim]{message}[/]")


def ok(message: str) -> None:
    console.print(f"[green]✓[/] {message}")


def auth_table(rows: list[tuple[str, str, str]]) -> None:
    table = Table(title="BYOK / local providers", expand=False)
    table.add_column("provider", style="bold")
    table.add_column("endpoint")
    table.add_column("status")
    for name, url, state in rows:
        color = "green" if state in {"configured", "local"} else "yellow"
        table.add_row(name, url, f"[{color}]{state}[/]")
    console.print(table)


def mcp_table(rows: list[tuple[str, str, str]]) -> None:
    table = Table(title="MCP servers", expand=False)
    table.add_column("name", style="bold")
    table.add_column("command")
    table.add_column("status")
    for name, cmdline, state in rows:
        table.add_row(name, cmdline, state)
    console.print(table)


def session_table(rows: list[tuple[str, str, str, str]]) -> None:
    table = Table(title="Sessions")
    table.add_column("id")
    table.add_column("updated")
    table.add_column("model")
    table.add_column("title")
    for row in rows:
        table.add_row(*row)
    console.print(table)


def help_text() -> str:
    return """
**REPL**
- `/help` `/status` `/tools`
- `/model NAME` `/provider NAME`
- `/mode build|plan`
- `/qa` `/qa on` `/qa off`
- `/compact` `/compact hard` — shrink conversation
- `/cost` — token usage this session
- `/undo` — revert last agent edits
- `/diff` — last edits or git diff
- `/review [focus]` — plan-mode review
- `/ask <question>` — read-only Q&A
- `/retry` — repeat last task
- `/last` — reprint last assistant reply
- `/alias` `/budget` `/share` `/shares`
- `/theme NAME` `/quiet` `/quiet on|off`
- `/commands` `/memory`
- `/bash allow|ask|deny`
- `/mcp` — configured MCP servers
- `/sessions` `/resume ID` `/export [path]`
- `/init` `/clear` `/exit`
- Custom: `.forge/commands/*.md` → `/name`
- Ctrl+C stops the current turn

**CLI**
`forge run "fix the failing tests"` · `forge run --plan "…"`
`forge ask "where is auth handled?"`
`forge ci --task "..."` · `forge undo` · `forge diff`
`forge worktree add|list|remove NAME`
`forge qa` · `forge auth login openai` · `forge models` · `forge sessions`
`forge mcp` · `forge commands` · `forge memory` · `forge doctor`
`forge alias` · `forge budget` · `forge share` · `forge shares` · `forge theme`
""".strip()
