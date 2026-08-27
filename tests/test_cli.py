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
    assert main(["sessions", "rm", "--repo", str(tmp_path)]) == 2
    assert main(["providers"]) == 0
    assert main(["set"]) == 0
    assert main(["set", "provider", "mistralai"]) == 0
    assert main(["set", "api", "sk-test-cli"]) == 0
    assert main(["api", "sk-test-cli-2"]) == 0
    assert main(["set", "nope-vendor"]) == 2
    seen: dict = {}

    def fake_repl(root, cfg, session_id=None):
        seen["chat"] = True
        return 0

    monkeypatch.setattr("forge_code.cli.start_repl", fake_repl)
    assert main(["chat", "--repo", str(tmp_path)]) == 0
    assert seen["chat"] is True
    try:
        main(["find"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("find without query should exit")


def test_bare_forge_opens_menu(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    hit: dict = {}

    def fake_menu(root, cfg):
        hit["menu"] = True
        return 0

    def fake_repl(root, cfg, session_id=None):
        hit["repl"] = session_id
        return 0

    monkeypatch.setattr("forge_code.cli.start_menu", fake_menu)
    monkeypatch.setattr("forge_code.cli.start_repl", fake_repl)
    assert main(["--repo", str(tmp_path)]) == 0
    assert hit == {"menu": True}
    assert main(["--repl", "--repo", str(tmp_path)]) == 0
    assert hit.get("repl") is None
    monkeypatch.setenv("FORGE_MENU", "0")
    hit.clear()
    assert main(["--repo", str(tmp_path)]) == 0
    assert hit == {"repl": None}


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


def test_run_model_and_stdin(tmp_path, monkeypatch) -> None:
    import io

    from forge_code.agent import TurnResult

    seen: dict = {}

    def fake_run(self, history, task):
        seen["model"] = self.cfg.model
        seen["provider"] = self.cfg.provider
        seen["task"] = task
        return TurnResult(text="ok")

    monkeypatch.setattr("forge_code.cli.Agent.run", fake_run)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    assert main(
        ["run", "--model", "fast", "--provider", "ollama", "inspect", "--repo", str(tmp_path)]
    ) == 0
    assert seen["model"] == "fast"
    assert seen["provider"] == "ollama"
    monkeypatch.setattr("sys.stdin", io.StringIO("from pipe\n"))
    assert main(["run", "-", "--repo", str(tmp_path)]) == 0
    assert seen["task"] == "from pipe"


def test_continue_latest(tmp_path, monkeypatch) -> None:
    from forge_code.session import new_session, save_session

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    first = new_session(tmp_path)
    first.touch("old")
    save_session(tmp_path, first)
    second = new_session(tmp_path)
    second.touch("new")
    save_session(tmp_path, second)
    seen: dict = {}

    def fake_repl(root, cfg, session_id=None):
        seen["id"] = session_id
        seen["model"] = cfg.model
        return 0

    monkeypatch.setattr("forge_code.cli.start_repl", fake_repl)
    assert main(["--continue", "--repo", str(tmp_path)]) == 0
    assert seen["id"] == second.id
    assert main(["-c", "--model", "local", "--repo", str(tmp_path)]) == 0
    assert seen["model"] == "local"


def test_sessions_rm_cli(tmp_path, monkeypatch) -> None:
    from forge_code.session import list_sessions, new_session

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    session = new_session(tmp_path)
    assert main(["sessions", "rm", session.id[:6], "--repo", str(tmp_path)]) == 0
    assert list_sessions(tmp_path) == []


def test_contribute_cli(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("USER", "tester")
    urls: list[str] = []
    monkeypatch.setattr(
        "webbrowser.open", lambda url, *a, **k: urls.append(url) or True
    )
    assert main(["contribute"]) == 0
    assert urls == []
    assert main(["contribute", "code"]) == 0
    assert urls == ["https://github.com/DarioDGR12/Forge-Code"]
    urls.clear()
    assert main(["contribute", "recommend", "please", "add", "vim"]) == 0
    assert urls
    assert urls[0].startswith("mailto:dariopro.1212@gmail.com?")
    saved = list((tmp_path / "data" / "forge-code" / "contributions").glob("*.md"))
    assert saved
    assert "please add vim" in saved[0].read_text(encoding="utf-8")
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(""))
    assert main(["contribute", "recommend"]) == 2


def test_set_lang_cli(tmp_path, monkeypatch) -> None:
    from forge_code.config import load_config

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("FORGE_LANG", raising=False)
    assert main(["set", "lang", "es"]) == 0
    assert load_config().lang == "es"
    assert main(["set", "lang", "nope"]) == 2
    assert main(["set", "lang"]) == 0
    assert main(["set", "lang", "auto"]) == 0
    assert load_config().lang == "auto"


def test_context_and_terminal_cli(tmp_path) -> None:
    (tmp_path / "README.md").write_text("# CLI ctx\n", encoding="utf-8")
    assert main(["context", "--repo", str(tmp_path)]) == 0
    assert (tmp_path / ".forge" / "context.md").is_file()
    assert main(["context", "--refresh", "--repo", str(tmp_path)]) == 0
    assert main(["terminal", "--repo", str(tmp_path)]) == 0
    assert main(["files", "--repo", str(tmp_path)]) == 0

