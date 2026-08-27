# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from forge_code import __version__
from forge_code.paths import data_dir

FEEDBACK_EMAIL = "dariopro.1212@gmail.com"
GITHUB_REPO = "https://github.com/DarioDGR12/Forge-Code"
CLONE_URL = "https://github.com/DarioDGR12/Forge-Code.git"
MAX_MAILTO = 1_800


def mailto_url(subject: str, body: str) -> str:
    text = body if len(body) <= MAX_MAILTO else body[:MAX_MAILTO] + "\n… [truncated]"
    return f"mailto:{FEEDBACK_EMAIL}?subject={quote(subject)}&body={quote(text)}"


def contribute_guide() -> str:
    return (
        f"Forge is Apache 2.0. Fork, branch, then send a PR.\n"
        f"git clone {CLONE_URL}\n"
        f"pip install -e \".[dev]\" && pytest\n"
        f"git commit -s\n"
        f"{GITHUB_REPO}\n"
        f"Questions: {FEEDBACK_EMAIL}"
    )


def save_recommendation(message: str, name: str = "") -> Path:
    folder = data_dir() / "contributions"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = folder / f"{stamp}.md"
    who = name.strip() or "anonymous"
    path.write_text(
        f"# Forge recommendation\n\n"
        f"- from: {who}\n"
        f"- at: {stamp}\n"
        f"- forge: {__version__}\n"
        f"- to: {FEEDBACK_EMAIL}\n\n"
        f"{message.strip()}\n",
        encoding="utf-8",
    )
    return path


def format_recommendation(message: str, name: str = "") -> tuple[str, str]:
    who = name.strip() or "anonymous"
    subject = f"Forge recommendation from {who}"
    body = (
        f"From: {who}\n"
        f"Forge: {__version__}\n"
        f"Repo: {GITHUB_REPO}\n\n"
        f"{message.strip()}\n"
    )
    return subject, body


def send_recommendation(
    message: str,
    name: str = "",
    *,
    open_url=None,
) -> tuple[Path, bool]:
    text = message.strip()
    if not text:
        raise ValueError("empty recommendation")
    path = save_recommendation(text, name)
    subject, body = format_recommendation(text, name)
    extra = f"\n\nFull copy saved at: {path}"
    opener = open_url or webbrowser.open
    opened = False
    try:
        opened = bool(opener(mailto_url(subject, body + extra)))
    except Exception:
        opened = False
    return path, opened


def open_github(*, open_url=None) -> str:
    opener = open_url or webbrowser.open
    try:
        opener(GITHUB_REPO)
    except Exception:
        pass
    return GITHUB_REPO
