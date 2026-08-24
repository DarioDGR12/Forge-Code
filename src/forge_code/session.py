# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from forge_code.models import Message, ToolCall
from forge_code.paths import sessions_dir


@dataclass
class Session:
    id: str
    repo: str
    created_at: str
    messages: list[Message] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "repo": self.repo,
            "created_at": self.created_at,
            "messages": [_message_dict(message) for message in self.messages],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Session:
        return cls(
            id=data["id"],
            repo=data.get("repo") or "",
            created_at=data.get("created_at") or "",
            messages=[_message_from(item) for item in data.get("messages") or []],
        )


def new_session(repo: Path) -> Session:
    now = datetime.now(timezone.utc).isoformat()
    session = Session(id=uuid4().hex[:12], repo=str(repo.resolve()), created_at=now)
    save_session(repo, session)
    return session


def save_session(repo: Path, session: Session) -> Path:
    path = sessions_dir(repo) / f"{session.id}.json"
    path.write_text(json.dumps(session.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def load_session(repo: Path, session_id: str) -> Session:
    path = sessions_dir(repo) / f"{session_id}.json"
    return Session.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _message_dict(message: Message) -> dict:
    payload = asdict(message)
    return payload


def _message_from(data: dict) -> Message:
    calls = [
        ToolCall(id=item["id"], name=item["name"], arguments=item.get("arguments") or {})
        for item in data.get("tool_calls") or []
    ]
    return Message(
        role=data.get("role") or "user",
        content=data.get("content") or "",
        tool_calls=calls,
        tool_call_id=data.get("tool_call_id") or "",
        name=data.get("name") or "",
    )
