# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.models import Message
from forge_code.session import export_markdown, list_sessions, load_session, new_session, save_session, search_sessions


def test_session_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    session = new_session(tmp_path, provider="ollama", model="local")
    session.messages.append(Message(role="user", content="hello"))
    session.touch("hello")
    save_session(tmp_path, session)

    loaded = load_session(tmp_path, session.id)
    assert loaded.messages[0].content == "hello"
    listed = list_sessions(tmp_path)
    assert listed[0].id == session.id
    md = export_markdown(loaded)
    assert "hello" in md
    assert session.id in md


def test_search_sessions(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    session = new_session(tmp_path, provider="ollama", model="local")
    session.messages.append(Message(role="user", content="where is auth handled?"))
    session.messages.append(Message(role="assistant", content="in src/auth.py"))
    session.touch("auth question")
    save_session(tmp_path, session)
    hits = search_sessions(tmp_path, "auth")
    assert hits
    assert any("auth.py" in hit.snippet or hit.role == "title" for hit in hits)
    assert search_sessions(tmp_path, "no-such-thing") == []
    assert search_sessions(tmp_path, "   ") == []
