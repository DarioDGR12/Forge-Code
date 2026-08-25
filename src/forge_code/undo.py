# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path

STACK = Path(".forge") / "undo.json"


@dataclass
class Snapshot:
    kind: str
    ref: str = ""
    created: list[str] = field(default_factory=list)
    files: dict[str, str | None] = field(default_factory=dict)
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Snapshot:
        return cls(
            kind=str(data.get("kind") or "files"),
            ref=str(data.get("ref") or ""),
            created=list(data.get("created") or []),
            files=dict(data.get("files") or {}),
            note=str(data.get("note") or ""),
        )


def is_git(root: Path) -> bool:
    if (root / ".git").exists():
        return True
    code, out = _git(root, ["rev-parse", "--is-inside-work-tree"])
    return code == 0 and out.strip() == "true"


def checkpoint(root: Path, note: str = "") -> Snapshot:
    if is_git(root):
        _, stash = _git(root, ["stash", "create"])
        _, head = _git(root, ["rev-parse", "HEAD"])
        snap = Snapshot(kind="git", ref=stash or head, note=note)
    else:
        snap = Snapshot(kind="files", note=note)
    _push(root, snap)
    return snap


def remember_write(root: Path, rel: str, existed: bool, previous: str | None) -> None:
    stack = load_stack(root)
    if not stack:
        return
    snap = stack[-1]
    if not existed:
        if rel not in snap.created:
            snap.created.append(rel)
    elif rel not in snap.files:
        snap.files[rel] = previous
    _write_stack(root, stack)


def undo_last(root: Path) -> str:
    stack = load_stack(root)
    if not stack:
        return "nothing to undo"
    snap = stack.pop()
    if snap.kind == "git" and snap.ref:
        code, out = _git(root, ["checkout", snap.ref, "--", "."])
        if code != 0:
            _write_stack(root, stack + [snap])
            return f"error: {out}"
    for rel, content in snap.files.items():
        path = root / rel
        if content is None:
            if path.exists():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    for rel in snap.created:
        path = root / rel
        if path.is_file():
            path.unlink()
    _write_stack(root, stack)
    return f"undid {snap.note or snap.kind} ({snap.ref or 'files'})"


def load_stack(root: Path) -> list[Snapshot]:
    path = root / STACK
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [Snapshot.from_dict(item) for item in raw]


def _push(root: Path, snap: Snapshot) -> None:
    stack = load_stack(root)
    stack.append(snap)
    _write_stack(root, stack[-20:])


def _write_stack(root: Path, stack: list[Snapshot]) -> None:
    path = root / STACK
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([item.to_dict() for item in stack], indent=2) + "\n", encoding="utf-8")


def _git(root: Path, args: list[str]) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 1, ""
    text = ((completed.stdout or "") + (completed.stderr or "")).strip()
    return completed.returncode, text if completed.returncode else (completed.stdout or "").strip()
