# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.models import Message
from forge_code.session import new_session, save_session, share_session


def test_share_writes_markdown(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    session = new_session(tmp_path, provider="ollama", model="local")
    session.messages.append(Message(role="user", content="hello"))
    session.touch("hello")
    save_session(tmp_path, session)
    path = share_session(tmp_path, session)
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert session.id in text
    assert "hello" in text
    assert "tokens:" in text
