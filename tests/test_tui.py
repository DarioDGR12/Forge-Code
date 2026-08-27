# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.config import AppConfig, load_config, resolve_api_key
from forge_code.providers.catalog import DEFAULT_PROVIDERS
from forge_code.tui import choose_index, start_menu


class _Choices:
    def __init__(self, indexes: list[int | None]) -> None:
        self.indexes = list(indexes)

    def __call__(self, title: str, options: list[str], extra: str = "") -> int | None:
        return self.indexes.pop(0)


def test_menu_provider_api_opens_chat(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.delenv("FORGE_API_KEY", raising=False)
    monkeypatch.delenv("FORGE_PROVIDER", raising=False)
    opened: list[tuple[str, str | None]] = []

    def fake_chat(root, cfg, session_id=None):
        opened.append((cfg.provider, session_id))
        return 0

    mistral = list(DEFAULT_PROVIDERS).index("mistral")
    # home → providers, vendor list → mistral, after chat home → quit
    start_menu(
        tmp_path,
        AppConfig(),
        choose=_Choices([0, mistral, 5]),
        ask=lambda _prompt: "sk-from-menu",
        chat=fake_chat,
    )
    cfg = load_config()
    assert cfg.provider == "mistral"
    assert resolve_api_key(cfg) == "sk-from-menu"
    assert opened == [("mistral", None)]


def test_menu_local_provider_skips_api(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("FORGE_PROVIDER", raising=False)
    opened: list[str] = []

    def fake_chat(root, cfg, session_id=None):
        opened.append(cfg.provider)
        return 0

    ollama = list(DEFAULT_PROVIDERS).index("ollama")
    start_menu(
        tmp_path,
        AppConfig(),
        choose=_Choices([0, ollama, 5]),
        ask=lambda _prompt: "SHOULD_NOT_RUN",
        chat=fake_chat,
    )
    assert opened == ["ollama"]
    assert load_config().provider == "ollama"


def test_menu_chats_new(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    seen: list[str | None] = []

    def fake_chat(root, cfg, session_id=None):
        seen.append(session_id)
        return 0

    # home → chats, chats → new chat, home → quit
    start_menu(
        tmp_path,
        AppConfig(),
        choose=_Choices([1, 0, 5]),
        ask=lambda _prompt: "",
        chat=fake_chat,
    )
    assert seen == [None]


def test_numbered_choose(monkeypatch) -> None:
    import io
    import sys

    monkeypatch.setattr(sys, "stdin", io.StringIO("2\n"))
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    assert choose_index("home", ["a", "b", "c"]) == 1
