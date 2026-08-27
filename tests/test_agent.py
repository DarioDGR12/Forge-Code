# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.agent import Agent
from forge_code.config import AppConfig, QAConfig
from forge_code.models import Completion, Message, ToolCall


def test_agent_edits_then_stops(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("hello\n", encoding="utf-8")
    calls = iter(
        [
            Completion(
                message=Message(
                    role="assistant",
                    content="",
                    tool_calls=[
                        ToolCall(
                            id="1",
                            name="edit_file",
                            arguments={
                                "path": "note.txt",
                                "old_string": "hello",
                                "new_string": "hola",
                            },
                        )
                    ],
                ),
                finish="tool",
            ),
            Completion(
                message=Message(role="assistant", content="Updated the greeting."),
                finish="stop",
            ),
        ]
    )

    def fake_complete(_cfg, _messages, _tools):
        return next(calls)

    cfg = AppConfig(provider="ollama", model="local", qa=QAConfig(auto=False))
    agent = Agent(tmp_path, cfg, complete_fn=fake_complete)
    result = agent.run([], "say hola")
    assert "Updated" in result.text
    assert (tmp_path / "note.txt").read_text(encoding="utf-8") == "hola\n"
    assert "note.txt" in result.writes
    assert (tmp_path / "files" / "note.txt").is_file()
    assert (tmp_path / "files" / "note.txt").read_text(encoding="utf-8") == "hola\n"


def test_agent_auto_qa_feeds_failure(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\nversion='0'\n", encoding="utf-8")
    (tmp_path / "bad.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_bad.py").write_text(
        "from bad import add\n\ndef test_add():\n    assert add(2, 3) == 5\n",
        encoding="utf-8",
    )

    stage = {"n": 0}

    def fake_complete(_cfg, messages, _tools):
        stage["n"] += 1
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        if stage["n"] == 1:
            return Completion(
                message=Message(
                    role="assistant",
                    tool_calls=[
                        ToolCall(
                            id="1",
                            name="write_file",
                            arguments={"path": "bad.py", "content": "def add(a, b):\n    return a - b\n"},
                        )
                    ],
                ),
                finish="tool",
            )
        if "Integrated QA failed" in last_user and not stage.get("fixed"):
            stage["fixed"] = True
            return Completion(
                message=Message(
                    role="assistant",
                    tool_calls=[
                        ToolCall(
                            id="2",
                            name="write_file",
                            arguments={"path": "bad.py", "content": "def add(a, b):\n    return a + b\n"},
                        )
                    ],
                ),
                finish="tool",
            )
        return Completion(message=Message(role="assistant", content="fixed"), finish="stop")

    cfg = AppConfig(provider="ollama", model="local", qa=QAConfig(auto=True, timeout=60))
    agent = Agent(tmp_path, cfg, complete_fn=fake_complete, max_steps=8)
    result = agent.run([], "fix add")
    assert result.text == "fixed"
    assert (tmp_path / "bad.py").read_text(encoding="utf-8") == "def add(a, b):\n    return a + b\n"
    assert result.qa is not None
    assert result.qa.ok


def test_agent_expands_mentions(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("hello from disk\n", encoding="utf-8")
    seen: list[str] = []

    def fake_complete(_cfg, messages, _tools):
        seen.append(messages[-1].content)
        return Completion(message=Message(role="assistant", content="ok"), finish="stop")

    cfg = AppConfig(provider="ollama", model="local", qa=QAConfig(auto=False))
    Agent(tmp_path, cfg, complete_fn=fake_complete).run([], "look at @note.txt")
    assert "hello from disk" in seen[0]
    assert "<attached files>" in seen[0]


def test_agent_refreshes_context_on_marker_write(tmp_path: Path) -> None:
    forge = tmp_path / ".forge"
    forge.mkdir()
    (forge / "context.md").write_text("# old\n", encoding="utf-8")
    calls = iter(
        [
            Completion(
                message=Message(
                    role="assistant",
                    tool_calls=[
                        ToolCall(
                            id="1",
                            name="write_file",
                            arguments={
                                "path": "pyproject.toml",
                                "content": "[project]\nname='demo'\nversion='0'\n",
                            },
                        )
                    ],
                ),
                finish="tool",
            ),
            Completion(
                message=Message(role="assistant", content="mapped"),
                finish="stop",
            ),
        ]
    )

    def fake_complete(_cfg, _messages, _tools):
        return next(calls)

    cfg = AppConfig(provider="ollama", model="local", qa=QAConfig(auto=False))
    Agent(tmp_path, cfg, complete_fn=fake_complete).run([], "add pyproject")
    text = (forge / "context.md").read_text(encoding="utf-8")
    assert "python" in text
    assert "# old" not in text
