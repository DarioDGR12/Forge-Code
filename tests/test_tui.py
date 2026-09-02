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
        choose=_Choices([0, mistral, 8]),
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
        choose=_Choices([0, ollama, 8]),
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
        choose=_Choices([1, 0, 8]),
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


def test_menu_contributions_recommend(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    urls: list[str] = []
    prompts = ["Ada", "please add vim keys"]

    start_menu(
        tmp_path,
        AppConfig(),
        choose=_Choices([5, 0, 2, 8]),
        ask=lambda _prompt: prompts.pop(0),
        chat=lambda *_a, **_k: 0,
        open_url=lambda url: urls.append(url) or True,
    )
    assert urls
    assert any("mailto:dariopro.1212@gmail.com" in url for url in urls)
    saved = list((tmp_path / "data" / "forge-code" / "contributions").glob("*.md"))
    assert len(saved) == 1
    text = saved[0].read_text(encoding="utf-8")
    assert "Ada" in text
    assert "vim keys" in text
    assert "dariopro.1212@gmail.com" in text


def test_menu_contributions_code(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    urls: list[str] = []
    start_menu(
        tmp_path,
        AppConfig(),
        choose=_Choices([5, 1, 2, 8]),
        ask=lambda _prompt: "",
        chat=lambda *_a, **_k: 0,
        open_url=lambda url: urls.append(url) or True,
    )
    assert urls == ["https://github.com/DarioDGR12/Forge-Code"]


def test_menu_contributions_empty_skips_mail(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    urls: list[str] = []
    start_menu(
        tmp_path,
        AppConfig(),
        choose=_Choices([5, 0, 2, 8]),
        ask=lambda _prompt: "",
        chat=lambda *_a, **_k: 0,
        open_url=lambda url: urls.append(url) or True,
    )
    assert urls == []
    folder = tmp_path / "data" / "forge-code" / "contributions"
    assert not folder.exists() or list(folder.glob("*.md")) == []


def test_menu_help_about(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    # home → help, help → about, help → back, home → quit
    assert (
        start_menu(
            tmp_path,
            AppConfig(),
            choose=_Choices([6, 0, 4, 8]),
            ask=lambda _prompt: "",
            chat=lambda *_a, **_k: 0,
        )
        == 0
    )


def test_menu_config_language(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("FORGE_LANG", raising=False)
    # home → config, config → language (auto→en), config → back, home → quit
    start_menu(
        tmp_path,
        AppConfig(),
        choose=_Choices([3, 4, 5, 8]),
        ask=lambda _prompt: "",
        chat=lambda *_a, **_k: 0,
    )
    assert load_config().lang == "en"


def test_menu_resume_last_chat(tmp_path: Path, monkeypatch) -> None:
    from forge_code.session import new_session, save_session

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    session = new_session(tmp_path, provider="ollama", model="local")
    session.touch("last task")
    save_session(tmp_path, session)
    seen: list[str | None] = []

    def fake_chat(root, cfg, session_id=None):
        seen.append(session_id)
        return 0

    # resume is home 0 when a session exists; quit is 9
    start_menu(
        tmp_path,
        AppConfig(),
        choose=_Choices([0, 9]),
        ask=lambda _prompt: "",
        chat=fake_chat,
    )
    assert seen == [session.id]


def test_menu_chat_rename(tmp_path: Path, monkeypatch) -> None:
    from forge_code.session import load_session, new_session, save_session

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    session = new_session(tmp_path, provider="ollama", model="local")
    session.touch("old title")
    save_session(tmp_path, session)
    # home chats=2; chats session=2; actions rename=1; actions back=3; chats back=3; quit=9
    start_menu(
        tmp_path,
        AppConfig(),
        choose=_Choices([2, 2, 1, 3, 3, 9]),
        ask=lambda _prompt: "new title",
        chat=lambda *_a, **_k: 0,
    )
    assert load_session(tmp_path, session.id).title == "new title"


def test_menu_chat_delete(tmp_path: Path, monkeypatch) -> None:
    from forge_code.session import list_sessions, new_session, save_session

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    session = new_session(tmp_path, provider="ollama", model="local")
    session.touch("gone")
    save_session(tmp_path, session)
    # after delete, resume disappears so quit is 8; chats back is 2
    start_menu(
        tmp_path,
        AppConfig(),
        choose=_Choices([2, 2, 2, 0, 2, 8]),
        ask=lambda _prompt: "",
        chat=lambda *_a, **_k: 0,
    )
    assert list_sessions(tmp_path) == []


def test_menu_chat_search_opens(tmp_path: Path, monkeypatch) -> None:
    from forge_code.models import Message
    from forge_code.session import new_session, save_session

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    session = new_session(tmp_path, provider="ollama", model="local")
    session.messages.append(Message(role="user", content="where is auth handled?"))
    session.touch("auth question")
    save_session(tmp_path, session)
    seen: list[str | None] = []

    def fake_chat(root, cfg, session_id=None):
        seen.append(session_id)
        return 0

    # home chats=2; search=1; pick hit=0; open=0; quit=9
    start_menu(
        tmp_path,
        AppConfig(),
        choose=_Choices([2, 1, 0, 0, 9]),
        ask=lambda _prompt: "auth",
        chat=fake_chat,
    )
    assert seen == [session.id]


def test_menu_help_doctor(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setattr(
        "forge_code.doctor.probe_local",
        lambda: {"ollama": ["qwen2.5-coder"], "llamacpp": []},
    )
    # help=6; doctor=2; back=4; quit=8
    assert (
        start_menu(
            tmp_path,
            AppConfig(),
            choose=_Choices([6, 2, 4, 8]),
            ask=lambda _prompt: "",
            chat=lambda *_a, **_k: 0,
        )
        == 0
    )


def test_menu_onboard_local_provider(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("FORGE_PROVIDER", raising=False)
    ollama = list(DEFAULT_PROVIDERS).index("ollama")
    start_menu(
        tmp_path,
        AppConfig(),
        choose=_Choices([ollama, 8]),
        ask=lambda _prompt: "SHOULD_NOT_RUN",
        chat=lambda *_a, **_k: 0,
        onboard=True,
    )
    assert load_config().provider == "ollama"


def test_menu_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    # home → files, files → back, home → quit
    assert (
        start_menu(
            tmp_path,
            AppConfig(),
            choose=_Choices([4, 4, 8]),
            ask=lambda _prompt: "",
            chat=lambda *_a, **_k: 0,
        )
        == 0
    )
