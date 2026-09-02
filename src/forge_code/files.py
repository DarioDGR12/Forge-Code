# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

"""Last-turn files: copy-friendly listing + a visible ``files/`` drop folder."""

from __future__ import annotations

import json
from pathlib import Path

DIR_NAME = "files"
STATE_REL = Path(".forge") / "last-files.json"
MAX_LINES = 80
MAX_BYTES = 80_000

LEXERS = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "jsx",
    ".rs": "rust",
    ".go": "go",
    ".rb": "ruby",
    ".java": "java",
    ".json": "json",
    ".toml": "toml",
    ".md": "markdown",
    ".sh": "bash",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".css": "css",
    ".html": "html",
    ".sql": "sql",
}


def files_dir(root: Path) -> Path:
    return root / DIR_NAME


def save_turn(root: Path, writes: list[str]) -> list[str]:
    """Copy this turn's written files into ``files/`` and remember them for /copy."""
    rels: list[str] = []
    seen: set[str] = set()
    dest_root = files_dir(root)
    for raw in writes:
        rel = str(raw or "").strip().replace("\\", "/")
        if not rel or rel == "apply_patch" or rel in seen:
            continue
        if rel.split("/", 1)[0] == DIR_NAME:
            continue
        src = root / rel
        if not src.is_file():
            continue
        dest = dest_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
        seen.add(rel)
        rels.append(rel)
    if not rels:
        return []
    state = root / STATE_REL
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({"paths": rels}, indent=2) + "\n", encoding="utf-8")
    _write_index(dest_root, rels)
    return rels


def load_last(root: Path) -> list[str]:
    path = root / STATE_REL
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    paths = raw.get("paths") if isinstance(raw, dict) else None
    if not isinstance(paths, list):
        return []
    return [str(item) for item in paths if str(item).strip()]


def read_for_copy(root: Path, rel: str | None = None) -> tuple[str, str]:
    """Return (path, text) for clipboard. ``rel`` None → last file of the turn."""
    if rel:
        target = rel.strip()
    else:
        last = load_last(root)
        target = last[-1] if last else ""
    if not target:
        return "", ""
    for candidate in (root / target, files_dir(root) / target):
        if candidate.is_file():
            return target, candidate.read_text(encoding="utf-8", errors="replace")
    return target, ""


def peek_blocks(root: Path, rel: str | None = None, *, max_lines: int = MAX_LINES) -> str:
    """Fence the last written file, or ``rel`` if given."""
    if rel:
        targets = [rel.strip()]
    else:
        last = load_last(root)
        targets = last[-1:] if last else []
    return fence_blocks(root, targets, max_lines=max_lines)


def fence_blocks(root: Path, rels: list[str], *, max_lines: int = MAX_LINES) -> str:
    chunks: list[str] = []
    for rel in rels:
        path = root / rel
        if not path.is_file():
            path = files_dir(root) / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if len(text.encode("utf-8")) > MAX_BYTES:
            text = text[:MAX_BYTES] + "\n..."
        lines = text.splitlines()
        extra = ""
        if len(lines) > max_lines:
            text = "\n".join(lines[:max_lines])
            extra = f"\n... ({len(lines) - max_lines} more — /copy {rel})"
        lang = LEXERS.get(path.suffix.lower(), "")
        chunks.append(f"**`{rel}`**\n```{lang}\n{text.rstrip()}{extra}\n```")
    return "\n\n".join(chunks)


def _write_index(dest_root: Path, rels: list[str]) -> None:
    lines = [
        "# Forge files",
        "",
        "Copies of what the agent just wrote. Open this folder in Files / Finder.",
        "",
        "In the REPL: `/copy` copies the last file. `/peek` previews it. `/files` lists them. `/open` opens this folder.",
        "",
    ]
    for rel in rels:
        lines.append(f"- `{rel}`")
    lines.append("")
    (dest_root / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")


def copy_to_clipboard(text: str) -> bool:
    import shutil
    import subprocess

    for name, extra in (
        ("wl-copy", []),
        ("xclip", ["-selection", "clipboard"]),
        ("xsel", ["--clipboard", "--input"]),
        ("pbcopy", []),
    ):
        binary = shutil.which(name)
        if not binary:
            continue
        try:
            subprocess.run(
                [binary, *extra],
                input=text.encode("utf-8"),
                check=True,
                timeout=3,
            )
            return True
        except (OSError, subprocess.SubprocessError):
            continue
    return False


def open_path(path: Path) -> bool:
    """Open a file or folder in the desktop file manager."""
    import shutil
    import subprocess

    if not path.exists():
        return False
    for name in ("xdg-open", "open", "wslview"):
        binary = shutil.which(name)
        if not binary:
            continue
        try:
            subprocess.Popen(
                [binary, str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True
        except OSError:
            continue
    return False
