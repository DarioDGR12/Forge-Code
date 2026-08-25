# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import fnmatch
from pathlib import Path

DEFAULT_PATTERNS = (
    ".git/",
    ".hg/",
    ".svn/",
    ".venv/",
    "venv/",
    "node_modules/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".forge/",
    ".worktrees/",
    "dist/",
    "build/",
    "*.pyc",
    "*.pyo",
    "*.egg-info/",
    ".DS_Store",
    "*.min.js",
    "*.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "Cargo.lock",
    ".env",
    ".env.*",
    "*.pem",
    "*.p12",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.yaml",
    "secrets.yml",
)


class IgnoreMatcher:
    """gitignore-style matcher for .forgeignore plus safe defaults."""

    def __init__(self, root: Path, extra: list[str] | None = None):
        self.root = root.resolve()
        self.patterns: list[str] = list(DEFAULT_PATTERNS)
        for name in (".forgeignore", ".gitignore"):
            path = self.root / name
            if path.is_file():
                self.patterns.extend(_parse_ignore_file(path))
        if extra:
            self.patterns.extend(extra)

    def ignored(self, rel: str) -> bool:
        posix = rel.replace("\\", "/")
        while posix.startswith("./"):
            posix = posix[2:]
        posix = posix.lstrip("/")
        parts = posix.split("/")
        for pattern in self.patterns:
            if _match(posix, parts, pattern):
                return True
        return False

    def allowed_file(self, path: Path) -> bool:
        try:
            rel = path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return False
        return not self.ignored(rel)


def _parse_ignore_file(path: Path) -> list[str]:
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def _match(posix: str, parts: list[str], pattern: str) -> bool:
    pat = pattern.rstrip()
    directory_only = pat.endswith("/")
    pat = pat.rstrip("/")
    if directory_only:
        if any(fnmatch.fnmatch(part, pat.split("/")[-1]) for part in parts[:-1]):
            return True
        if posix.startswith(pat.rstrip("*") ) and len(parts) > 1:
            return True
    if "/" not in pat:
        return any(fnmatch.fnmatch(part, pat) for part in parts) or fnmatch.fnmatch(
            posix, pat
        )
    return fnmatch.fnmatch(posix, pat) or fnmatch.fnmatch(posix, pat.lstrip("/"))
