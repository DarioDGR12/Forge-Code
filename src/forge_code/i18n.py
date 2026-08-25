# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os

STRINGS = {
    "en": {
        "forging": "forging…",
        "interrupted": "interrupted — /undo reverts the last edits",
        "bye": "bye",
        "nothing_undo": "nothing to undo",
        "allow_bash": "allow bash `{cmd}`? [y/N] ",
        "denied_bash": "user denied bash",
    },
    "es": {
        "forging": "forjando…",
        "interrupted": "interrumpido — /undo revierte los últimos cambios",
        "bye": "adiós",
        "nothing_undo": "nada que deshacer",
        "allow_bash": "¿permitir bash `{cmd}`? [s/N] ",
        "denied_bash": "el usuario rechazó bash",
    },
}


def lang() -> str:
    raw = (os.environ.get("FORGE_LANG") or os.environ.get("LANG") or "en").lower()
    if raw.startswith("es"):
        return "es"
    return "en"


def t(key: str, **kwargs: str) -> str:
    table = STRINGS.get(lang()) or STRINGS["en"]
    text = table.get(key) or STRINGS["en"].get(key) or key
    return text.format(**kwargs) if kwargs else text
