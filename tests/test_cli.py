# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from forge_code.cli import main


def test_help_exits_zero() -> None:
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("argparse --help should SystemExit")


def test_version_exits_zero() -> None:
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("expected --version to exit")


def test_auth_status(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    assert main(["auth", "status"]) == 0


def test_qa_on_broken_example() -> None:
    assert main(["qa", "--repo", "examples/broken-add"]) == 1


def test_tools_lists_builtins() -> None:
    assert main(["tools"]) == 0


def test_sessions_empty(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    assert main(["sessions", "--repo", str(tmp_path)]) == 0


def test_undo_empty_repo(tmp_path) -> None:
    assert main(["undo", "--repo", str(tmp_path)]) == 0


def test_ci_requires_task(monkeypatch) -> None:
    monkeypatch.delenv("FORGE_TASK", raising=False)
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
    assert main(["ci"]) == 2


def test_mcp_lists_none(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    assert main(["mcp"]) == 0


def test_alias_budget_share_cli(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    assert main(["alias"]) == 0
    assert main(["alias", "set", "flash", "gpt-4.1-nano"]) == 0
    assert main(["budget"]) == 0
    assert main(["share", "--repo", str(tmp_path)]) == 2
    assert main(["shares", "--repo", str(tmp_path)]) == 0
    assert main(["theme"]) == 0
    assert main(["theme", "magenta"]) == 0
    assert main(["theme", "nope"]) == 2
    assert main(["find", "--repo", str(tmp_path), "nothing"]) == 0
    assert main(["sessions", "search", "--repo", str(tmp_path)]) == 2
    try:
        main(["find"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("find without query should exit")


def test_ask_and_worktree_cli(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    try:
        main(["ask"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("ask without question should exit")
    assert main(["worktree", "add", "x", "--repo", str(tmp_path)]) == 2
    assert main(["worktree", "list", "--repo", str(tmp_path)]) == 0


def test_run_plan_sets_mode(tmp_path, monkeypatch) -> None:
    from forge_code.agent import TurnResult

    seen: dict = {}

    def fake_run(self, history, task):
        seen["mode"] = self.cfg.mode
        seen["qa"] = self.cfg.qa.auto
        seen["task"] = task
        return TurnResult(text="ok")

    monkeypatch.setattr("forge_code.cli.Agent.run", fake_run)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    assert main(["ask", "where is add?", "--repo", str(tmp_path)]) == 0
    assert seen["mode"] == "plan"
    assert seen["qa"] is False
    assert seen["task"] == "where is add?"
    assert main(["run", "--plan", "inspect", "--repo", str(tmp_path)]) == 0
    assert seen["mode"] == "plan"


def test_run_quiet_hides_transcript(tmp_path, monkeypatch, capsys) -> None:
    from forge_code.agent import TurnResult

    def fake_run(self, history, task):
        return TurnResult(text="UNIQUE_QUIET_MARKER")

    monkeypatch.setattr("forge_code.cli.Agent.run", fake_run)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    assert main(["run", "inspect", "--repo", str(tmp_path)]) == 0
    assert "UNIQUE_QUIET_MARKER" in capsys.readouterr().out
    assert main(["run", "-q", "inspect", "--repo", str(tmp_path)]) == 0
    assert "UNIQUE_QUIET_MARKER" not in capsys.readouterr().out
    assert main(["ask", "-q", "where?", "--repo", str(tmp_path)]) == 0
    assert "UNIQUE_QUIET_MARKER" not in capsys.readouterr().out


def test_find_cli_hits(tmp_path, monkeypatch, capsys) -> None:
    from forge_code.models import Message
    from forge_code.session import new_session, save_session

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    session = new_session(tmp_path, provider="ollama", model="local")
    session.messages.append(Message(role="user", content="where is auth handled?"))
    session.touch("auth question")
    save_session(tmp_path, session)
    assert main(["find", "--repo", str(tmp_path), "auth"]) == 0
    out = capsys.readouterr().out
    assert session.id in out
    assert "auth" in out.lower()
    assert main(["sessions", "search", "auth", "--repo", str(tmp_path)]) == 0
    assert session.id in capsys.readouterr().out


def test_init_diff_commands_memory(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    assert main(["init", "--repo", str(tmp_path)]) == 0
    assert (tmp_path / "AGENTS.md").is_file()
    assert main(["commands", "--repo", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "/explain" in out
    assert main(["diff", "--repo", str(tmp_path)]) == 0
    assert main(["memory", "--repo", str(tmp_path)]) == 0


def test_mcp_lists_configured(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    (tmp_path / ".forge").mkdir()
    (tmp_path / ".forge" / "config.json").write_text(
        '{"mcp":{"docs":{"command":"npx","args":["-y","demo"]}}}\n',
        encoding="utf-8",
    )
    assert main(["mcp"]) == 0
    out = capsys.readouterr().out
    assert "docs" in out
    assert "npx" in out
