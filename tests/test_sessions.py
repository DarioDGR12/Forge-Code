# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.models import Message
from forge_code.session import (
    delete_session,
    export_markdown,
    latest_session,
    list_sessions,
    load_session,
    new_session,
    rename_session,
    resolve_session,
    save_session,
    search_sessions,
)


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


def test_resolve_latest_and_delete(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    first = new_session(tmp_path, provider="ollama", model="local")
    first.touch("older")
    save_session(tmp_path, first)
    second = new_session(tmp_path, provider="ollama", model="local")
    second.touch("newer")
    save_session(tmp_path, second)
    assert latest_session(tmp_path).id == second.id
    loaded = resolve_session(tmp_path, second.id[:6])
    assert loaded.id == second.id
    assert delete_session(tmp_path, second.id[:6]) == second.id
    assert latest_session(tmp_path).id == first.id
    renamed = rename_session(tmp_path, first.id, "renamed in tests")
    assert renamed.title == "renamed in tests"
    try:
        resolve_session(tmp_path, "nope")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("missing session should raise")
