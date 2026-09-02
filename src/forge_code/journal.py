# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

"""Turn journal: ``.forge/journal.md``."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

JOURNAL_REL = Path(".forge") / "journal.md"
MAX_BYTES = 40_000
TAIL_ENTRIES = 12


def journal_path(root: Path) -> Path:
    return root / JOURNAL_REL


def append_entry(
    root: Path,
    *,
    task: str,
    writes: list[str] | None = None,
    qa_ok: bool | None = None,
) -> Path:
    path = journal_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if qa_ok is True:
        qa = "qa pass"
    elif qa_ok is False:
        qa = "qa fail"
    else:
        qa = "qa —"
    shown = [w for w in (writes or []) if w][:8]
    files = ", ".join(shown) or "(none)"
    extra = len([w for w in (writes or []) if w]) - len(shown)
    if extra > 0:
        files += f" +{extra}"
    block = f"### {stamp}\n{(task or '').strip()[:240] or '(no task)'}\n{qa}  files: {files}\n"
    existing = ""
    if path.is_file():
        existing = path.read_text(encoding="utf-8", errors="replace")
    text = block + "\n" + existing
    path.write_text(text[:MAX_BYTES], encoding="utf-8")
    return path


def load_journal(root: Path, *, entries: int = TAIL_ENTRIES, query: str = "") -> str:
    path = journal_path(root)
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    chunks = [c.strip() for c in text.split("\n### ") if c.strip()]
    needle = (query or "").strip().lower()
    if needle:
        chunks = [c for c in chunks if needle in c.lower()]
    kept: list[str] = []
    for chunk in chunks[: max(1, entries)]:
        kept.append(chunk if chunk.startswith("### ") else "### " + chunk)
    return "\n\n".join(kept)


def last_entry(root: Path) -> str:
    return load_journal(root, entries=1)
