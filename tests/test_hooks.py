# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.agent import Agent
from forge_code.config import AppConfig, QAConfig
from forge_code.hooks import run_hook
from forge_code.models import Completion, Message, ToolCall


def test_run_hook_missing_is_empty(tmp_path: Path) -> None:
    assert run_hook(tmp_path, "pre_edit") == ""


def test_run_hook_unknown() -> None:
    assert run_hook(Path("."), "nope").startswith("error:")


def test_pre_edit_hook_blocks_write(tmp_path: Path) -> None:
    hook_dir = tmp_path / ".forge" / "hooks"
    hook_dir.mkdir(parents=True)
    hook = hook_dir / "pre_edit"
    hook.write_text("#!/bin/sh\necho blocked\nexit 2\n", encoding="utf-8")
    hook.chmod(0o755)
    (tmp_path / "note.txt").write_text("hello\n", encoding="utf-8")

    calls = iter(
        [
            Completion(
                message=Message(
                    role="assistant",
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
                message=Message(role="assistant", content="stopped"),
                finish="stop",
            ),
        ]
    )

    def fake_complete(_cfg, _messages, _tools):
        return next(calls)

    events: list[tuple[str, str]] = []
    cfg = AppConfig(provider="ollama", model="local", qa=QAConfig(auto=False))
    agent = Agent(
        tmp_path,
        cfg,
        complete_fn=fake_complete,
        on_event=lambda kind, msg: events.append((kind, msg)),
        attach_mcp=False,
    )
    result = agent.run([], "say hola")
    assert (tmp_path / "note.txt").read_text(encoding="utf-8") == "hello\n"
    assert "note.txt" not in result.writes
    assert any(kind == "hook" and "exited 2" in msg for kind, msg in events)


def test_post_turn_hook_runs(tmp_path: Path) -> None:
    hook_dir = tmp_path / ".forge" / "hooks"
    hook_dir.mkdir(parents=True)
    hook = hook_dir / "post_turn"
    hook.write_text(
        "#!/bin/sh\necho ran > \"$FORGE_ROOT/.forge/hook-ran\"\n",
        encoding="utf-8",
    )
    hook.chmod(0o755)

    def fake_complete(_cfg, _messages, _tools):
        return Completion(message=Message(role="assistant", content="ok"), finish="stop")

    cfg = AppConfig(provider="ollama", model="local", qa=QAConfig(auto=False))
    Agent(tmp_path, cfg, complete_fn=fake_complete, attach_mcp=False).run([], "hi")
    assert (tmp_path / ".forge" / "hook-ran").read_text(encoding="utf-8").strip() == "ran"
