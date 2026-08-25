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
        "no_diff": "no edits to diff",
        "no_commands": "no custom commands in .forge/commands",
        "empty_memory": "memory is empty",
        "ask_usage": "usage: /ask <question>",
        "nothing_retry": "nothing to retry",
        "no_reply": "no assistant reply yet",
        "budget_hit": "stopped — session budget reached",
        "shared": "wrote {path}",
        "no_matches": "no matches",
        "find_usage": "usage: /find <query>",
        "pinned": "pinned to memory",
    },
    "es": {
        "forging": "forjando…",
        "interrupted": "interrumpido — /undo revierte los últimos cambios",
        "bye": "adiós",
        "nothing_undo": "nada que deshacer",
        "allow_bash": "¿permitir bash `{cmd}`? [s/N] ",
        "denied_bash": "el usuario rechazó bash",
        "no_diff": "nada que comparar",
        "no_commands": "no hay comandos en .forge/commands",
        "empty_memory": "la memoria está vacía",
        "ask_usage": "uso: /ask <pregunta>",
        "nothing_retry": "nada que repetir",
        "no_reply": "aún no hay respuesta",
        "budget_hit": "detenido — presupuesto de la sesión agotado",
        "shared": "escrito {path}",
        "no_matches": "sin coincidencias",
        "find_usage": "uso: /find <consulta>",
        "pinned": "anclado en memoria",
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
