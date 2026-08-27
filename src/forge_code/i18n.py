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
        "copied_file": "copied {path}",
        "empty_files": "no files this turn — ask Forge to write something first",
        "no_clipboard": "no clipboard tool; reprinting",
        "sessions_rm_usage": "usage: /sessions rm <id>",
        "cannot_delete_current": "cannot delete the current session; /new first",
        "deleted": "deleted {id}",
        "set_usage": "usage: forge set provider NAME  |  forge set api KEY  |  forge set model NAME  |  forge set lang auto|en|es",
        "provider_set": "provider → {provider}  model {model}",
        "need_api": "no API key. next:  forge set api YOUR_KEY",
        "need_api_repl": "no API key. paste:  /api YOUR_KEY",
        "api_saved": "api key saved for {provider}",
        "api_usage": "usage: /api YOUR_KEY",
        "menu_home": "home",
        "menu_providers": "providers",
        "menu_chats": "chats",
        "menu_models": "models",
        "menu_config": "config",
        "menu_contributions": "contributions",
        "menu_forge": "forge",
        "menu_quit": "quit",
        "menu_back": "back",
        "menu_new_chat": "new chat",
        "menu_resume": "resume",
        "menu_search_chats": "search",
        "menu_search_prompt": "search chats",
        "menu_open_chat": "open",
        "menu_rename_chat": "rename",
        "menu_delete_chat": "delete",
        "menu_confirm_delete": "delete this chat?",
        "menu_confirm_yes": "yes, delete",
        "untitled": "(untitled)",
        "onboard_welcome": "no API key yet — pick a provider (ollama needs none) or paste a key",
        "menu_type_model": "type a model name",
        "menu_api": "paste the API key for {provider}",
        "menu_need_key": "no key",
        "menu_hint": "↑↓ enter to select · number + enter · q back",
        "contrib_title": "contributions",
        "contrib_recommend": "recommend an improvement",
        "contrib_code": "contribute code (GitHub)",
        "contrib_name_prompt": "your name (optional)",
        "contrib_body_hint": "this opens your mail app to {email} — hit Send",
        "contrib_body_prompt": "your recommendation",
        "contrib_empty": "empty — nothing sent",
        "contrib_saved": "saved a local copy at {path}",
        "contrib_mailto_opened": "opened mail to {email} — hit Send",
        "contrib_mailto_failed": "could not open mail. write to {email}",
        "contrib_opening_github": "opening GitHub…",
        "contrib_cli_help": "Recommendations go to {email}.  forge contribute recommend \"your idea\"  ·  forge contribute code",
        "lang_set": "language → {lang}",
        "menu_help": "help",
        "help_title": "help",
        "help_about": "about",
        "help_commands": "commands",
        "help_doctor": "doctor",
        "help_language": "language",
        "help_about_body": "Apache 2.0 terminal coding agent. BYOK or local models. Not affiliated with OpenCode or Anthropic.",
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
        "copied_file": "copiado {path}",
        "empty_files": "no hay archivos este turno — pide a Forge que escriba algo",
        "no_clipboard": "sin portapapeles; reimprimiendo",
        "sessions_rm_usage": "uso: /sessions rm <id>",
        "cannot_delete_current": "no se puede borrar la sesión actual; /new primero",
        "deleted": "borrada {id}",
        "set_usage": "uso: forge set provider NOMBRE  |  forge set api CLAVE  |  forge set model NOMBRE  |  forge set lang auto|en|es",
        "provider_set": "provider → {provider}  modelo {model}",
        "need_api": "falta la API. siguiente:  forge set api TU_CLAVE",
        "need_api_repl": "falta la API. pega:  /api TU_CLAVE",
        "api_saved": "clave guardada para {provider}",
        "api_usage": "uso: /api TU_CLAVE",
        "menu_home": "inicio",
        "menu_providers": "providers",
        "menu_chats": "chats",
        "menu_models": "models",
        "menu_config": "config",
        "menu_contributions": "contribuciones",
        "menu_forge": "forge",
        "menu_quit": "salir",
        "menu_back": "atrás",
        "menu_new_chat": "chat nuevo",
        "menu_resume": "continuar",
        "menu_search_chats": "buscar",
        "menu_search_prompt": "buscar chats",
        "menu_open_chat": "abrir",
        "menu_rename_chat": "renombrar",
        "menu_delete_chat": "borrar",
        "menu_confirm_delete": "¿borrar este chat?",
        "menu_confirm_yes": "sí, borrar",
        "untitled": "(sin título)",
        "onboard_welcome": "aún no hay API — elige un provider (ollama no pide clave) o pega una clave",
        "menu_type_model": "escribir un modelo",
        "menu_api": "pega la API de {provider}",
        "menu_need_key": "sin clave",
        "menu_hint": "↑↓ enter para elegir · número + enter · q atrás",
        "contrib_title": "contribuciones",
        "contrib_recommend": "recomendar una mejora",
        "contrib_code": "contribuir código (GitHub)",
        "contrib_name_prompt": "tu nombre (opcional)",
        "contrib_body_hint": "esto abre tu correo a {email} — pulsa Enviar",
        "contrib_body_prompt": "tu recomendación",
        "contrib_empty": "vacío — no se envió nada",
        "contrib_saved": "copia local guardada en {path}",
        "contrib_mailto_opened": "correo abierto a {email} — pulsa Enviar",
        "contrib_mailto_failed": "no se pudo abrir el correo. escribe a {email}",
        "contrib_opening_github": "abriendo GitHub…",
        "contrib_cli_help": "Las recomendaciones van a {email}.  forge contribute recommend \"tu idea\"  ·  forge contribute code",
        "lang_set": "idioma → {lang}",
        "menu_help": "ayuda",
        "help_title": "ayuda",
        "help_about": "acerca de",
        "help_commands": "comandos",
        "help_doctor": "doctor",
        "help_language": "idioma",
        "help_about_body": "Agente de código Apache 2.0 para la terminal. BYOK o modelos locales. No afiliado a OpenCode ni Anthropic.",
    },
}


_CONFIG_LANG = "auto"
_LANG_ORDER = ("auto", "en", "es")


def normalize_lang(value: str) -> str:
    raw = (value or "auto").strip().lower()
    if raw in {"es", "español", "espanol", "spanish"}:
        return "es"
    if raw in {"en", "english"}:
        return "en"
    if raw in {"auto", "system"}:
        return "auto"
    raise ValueError("language must be auto, en, or es")


def set_config_lang(code: str) -> str:
    global _CONFIG_LANG
    try:
        _CONFIG_LANG = normalize_lang(code)
    except ValueError:
        _CONFIG_LANG = "auto"
    return _CONFIG_LANG


def cycle_lang(current: str) -> str:
    try:
        idx = _LANG_ORDER.index(normalize_lang(current))
    except ValueError:
        idx = 0
    return _LANG_ORDER[(idx + 1) % len(_LANG_ORDER)]


def lang() -> str:
    env = os.environ.get("FORGE_LANG")
    if env:
        return "es" if env.lower().startswith("es") else "en"
    if _CONFIG_LANG.startswith("es"):
        return "es"
    if _CONFIG_LANG.startswith("en"):
        return "en"
    raw = (os.environ.get("LANG") or "en").lower()
    return "es" if raw.startswith("es") else "en"


def t(key: str, **kwargs: str) -> str:
    table = STRINGS.get(lang()) or STRINGS["en"]
    text = table.get(key) or STRINGS["en"].get(key) or key
    return text.format(**kwargs) if kwargs else text
