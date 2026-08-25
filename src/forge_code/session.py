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
from forge_code.usage import Usage


@dataclass
class Session:
    id: str
    repo: str
    created_at: str
    updated_at: str = ""
    title: str = ""
    provider: str = ""
    model: str = ""
    messages: list[Message] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "repo": self.repo,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "title": self.title,
            "provider": self.provider,
            "model": self.model,
            "messages": [_message_dict(message) for message in self.messages],
            "usage": self.usage.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Session:
        usage_raw = data.get("usage") or {}
        return cls(
            id=data["id"],
            repo=data.get("repo") or "",
            created_at=data.get("created_at") or "",
            updated_at=data.get("updated_at") or "",
            title=data.get("title") or "",
            provider=data.get("provider") or "",
            model=data.get("model") or "",
            messages=[_message_from(item) for item in data.get("messages") or []],
            usage=Usage(
                prompt_tokens=int(usage_raw.get("prompt_tokens") or 0),
                completion_tokens=int(usage_raw.get("completion_tokens") or 0),
            ),
        )

    def touch(self, title: str | None = None) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()
        if title and not self.title:
            self.title = title[:80]


def new_session(repo: Path, provider: str = "", model: str = "") -> Session:
    now = datetime.now(timezone.utc).isoformat()
    session = Session(
        id=uuid4().hex[:12],
        repo=str(repo.resolve()),
        created_at=now,
        updated_at=now,
        provider=provider,
        model=model,
    )
    save_session(repo, session)
    return session


def save_session(repo: Path, session: Session) -> Path:
    session.updated_at = session.updated_at or datetime.now(timezone.utc).isoformat()
    path = sessions_dir(repo) / f"{session.id}.json"
    path.write_text(json.dumps(session.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def load_session(repo: Path, session_id: str) -> Session:
    path = sessions_dir(repo) / f"{session_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"session not found: {session_id}")
    return Session.from_dict(json.loads(path.read_text(encoding="utf-8")))


def list_sessions(repo: Path) -> list[Session]:
    items: list[Session] = []
    for path in sessions_dir(repo).glob("*.json"):
        try:
            items.append(Session.from_dict(json.loads(path.read_text(encoding="utf-8"))))
        except (json.JSONDecodeError, KeyError):
            continue
    items.sort(key=lambda session: session.updated_at or session.created_at, reverse=True)
    return items


def export_markdown(session: Session) -> str:
    lines = [
        f"# Forge session `{session.id}`",
        "",
        f"- repo: `{session.repo}`",
        f"- created: {session.created_at}",
        f"- model: {session.provider}/{session.model}",
        f"- title: {session.title or '(untitled)'}",
        f"- tokens: {session.usage.total} ({session.usage.prompt_tokens} in / {session.usage.completion_tokens} out)",
        "",
    ]
    for message in session.messages:
        if message.role == "system":
            continue
        if message.role == "tool":
            lines.append(f"### tool `{message.name}`")
            lines.append("```")
            lines.append(message.content[:2000])
            lines.append("```")
            lines.append("")
            continue
        lines.append(f"### {message.role}")
        lines.append(message.content or "")
        lines.append("")
    return "\n".join(lines)


def share_session(root: Path, session: Session, dest: Path | None = None) -> Path:
    path = dest or (root / ".forge" / "shares" / f"{session.id}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(export_markdown(session), encoding="utf-8")
    return path


def _message_dict(message: Message) -> dict:
    return asdict(message)


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
