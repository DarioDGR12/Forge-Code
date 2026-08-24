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

console = Console()


def banner(cfg: AppConfig, repo: str) -> None:
    title = Text()
    title.append("Forge", style="bold cyan")
    title.append("  ", style="dim")
    title.append(f"v{__version__}", style="dim")
    body = (
        f"[dim]repo[/] {repo}\n"
        f"[dim]model[/] {cfg.provider}/{cfg.resolved_model()}\n"
        f"[dim]mode[/]  {cfg.mode}    [dim]qa[/] {'on' if cfg.qa.auto else 'off'}\n\n"
        "[dim]Type a task, or /help. This is not affiliated with OpenCode or Anthropic.[/]"
    )
    console.print(Panel(body, title=title, border_style="cyan", padding=(1, 2)))


def speak(text: str) -> None:
    if not text.strip():
        return
    console.print()
    console.print(Markdown(text))
    console.print()


def tool_line(message: str) -> None:
    console.print(f"  [cyan]▸[/] [dim]{message}[/]")


def qa_panel(report: QAReport) -> None:
    style = "green" if report.ok else "red"
    console.print(Panel(report.summary(), title="QA", border_style=style))


def error(message: str) -> None:
    console.print(f"[red]error[/] {message}")


def info(message: str) -> None:
    console.print(f"[dim]{message}[/]")


def auth_table(rows: list[tuple[str, str, str]]) -> None:
    table = Table(title="BYOK / local providers")
    table.add_column("provider")
    table.add_column("endpoint")
    table.add_column("status")
    for name, url, state in rows:
        color = "green" if state in {"configured", "local"} else "yellow"
        table.add_row(name, url, f"[{color}]{state}[/]")
    console.print(table)


def help_text() -> str:
    return """
**Commands**
- `/help` — this screen
- `/status` — repo, model, QA
- `/model NAME` — switch model
- `/provider NAME` — openai, anthropic, openrouter, groq, ollama, llamacpp, custom
- `/mode build|plan` — plan is read-only
- `/qa` — run the integrated test/lint suite
- `/qa on` / `/qa off` — auto-QA after edits
- `/init` — write AGENTS.md
- `/clear` — new conversation
- `/exit` — quit

**Non-interactive**
`forge run "fix the failing tests"`
`forge qa`
`forge auth login openai`
`forge models`
""".strip()
