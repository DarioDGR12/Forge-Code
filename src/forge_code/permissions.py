# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from forge_code.ignore import IgnoreMatcher

SECRET_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
    "credentials.json",
    "secrets.yaml",
    "secrets.yml",
    "service-account.json",
}

DANGEROUS_BASH = (
    re.compile(r"\brm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+)?/\s*$"),
    re.compile(r"\brm\s+-rf\s+/\b"),
    re.compile(r"\bmkfs\b"),
    re.compile(r"\bdd\s+if="),
    re.compile(r":\(\)\s*\{\s*:\|:\s*&\s*\}"),
    re.compile(r"\bshutdown\b"),
    re.compile(r"\breboot\b"),
    re.compile(r"curl\s+[^\n|]*\|\s*(ba)?sh"),
    re.compile(r"wget\s+[^\n|]*\|\s*(ba)?sh"),
    re.compile(r"\bchmod\s+-R\s+777\b"),
)


@dataclass
class PermissionConfig:
    bash: str = "allow"  # allow | deny | ask
    deny_globs: list[str] = field(
        default_factory=lambda: [".env", ".env.*", "*.pem", "**/id_rsa", "**/id_ed25519"]
    )


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str = ""


class PermissionGate:
    def __init__(self, root: Path, cfg: PermissionConfig | None = None):
        self.root = root
        self.cfg = cfg or PermissionConfig()
        self.ignore = IgnoreMatcher(root, extra=self.cfg.deny_globs)

    def review_write(self, rel: str) -> Decision:
        name = Path(rel).name
        if name in SECRET_NAMES:
            return Decision(False, f"refusing to write secret-bearing file {rel}")
        if self.ignore.ignored(rel):
            return Decision(False, f"path is ignored or denied: {rel}")
        return Decision(True)

    def review_read(self, rel: str) -> Decision:
        name = Path(rel).name
        if name in SECRET_NAMES:
            return Decision(False, f"refusing to read secret-bearing file {rel}")
        return Decision(True)

    def review_bash(self, command: str) -> Decision:
        if self.cfg.bash == "deny":
            return Decision(False, "bash is disabled by policy")
        text = command.strip()
        if not text:
            return Decision(False, "empty command")
        for cre in DANGEROUS_BASH:
            if cre.search(text):
                return Decision(False, "command matches a destructive pattern")
        return Decision(True)
