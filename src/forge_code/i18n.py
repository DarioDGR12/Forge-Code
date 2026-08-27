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
        "new_session": "new session {id}",
        "rename_usage": "usage: /rename <title>",
        "renamed": "renamed → {title}",
        "copied": "copied",
        "no_clipboard": "no clipboard tool; reprinting",
        "sessions_rm_usage": "usage: /sessions rm <id>",
        "cannot_delete_current": "cannot delete the current session; /new first",
        "deleted": "deleted {id}",
        "set_usage": "usage: forge set provider NAME  |  forge set api KEY  |  forge set model NAME",
        "provider_set": "provider → {provider}  model {model}",
        "need_api": "no API key. next:  forge set api YOUR_KEY",
        "need_api_repl": "no API key. paste:  /api YOUR_KEY",
        "api_saved": "api key saved for {provider}",
        "api_usage": "usage: /api YOUR_KEY",
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
        "new_session": "sesión nueva {id}",
        "rename_usage": "uso: /rename <título>",
        "renamed": "renombrada → {title}",
        "copied": "copiado",
        "no_clipboard": "sin portapapeles; reimprimiendo",
        "sessions_rm_usage": "uso: /sessions rm <id>",
        "cannot_delete_current": "no se puede borrar la sesión actual; /new primero",
        "deleted": "borrada {id}",
        "set_usage": "uso: forge set provider NOMBRE  |  forge set api CLAVE  |  forge set model NOMBRE",
        "provider_set": "provider → {provider}  modelo {model}",
        "need_api": "falta la API. siguiente:  forge set api TU_CLAVE",
        "need_api_repl": "falta la API. pega:  /api TU_CLAVE",
        "api_saved": "clave guardada para {provider}",
        "api_usage": "uso: /api TU_CLAVE",
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
