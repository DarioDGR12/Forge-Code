# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.tools.bash import run_bash
from forge_code.tools.registry import default_registry
from forge_code.tools.terminal import load_cwd, load_terminal


def test_bash_logs_and_persists_cwd(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "ok.txt").write_text("hi\n", encoding="utf-8")
    tools = default_registry()
    first = tools.execute(tmp_path, "bash", {"command": "pwd"})
    assert first.startswith("exit 0")
    log = load_terminal(tmp_path)
    assert "$ pwd" in log
    cd = tools.execute(tmp_path, "bash", {"command": "cd src"})
    assert cd.startswith("exit 0")
    cwd = load_cwd(tmp_path)
    assert cwd.name == "src"
    listed = tools.execute(tmp_path, "bash", {"command": "ls"})
    assert "ok.txt" in listed
    redacted = run_bash(tmp_path, {"command": "echo api_key=secret-value"})
    assert "secret-value" in redacted
    assert "secret-value" not in load_terminal(tmp_path)
    assert "api_key=***" in load_terminal(tmp_path)
    escaped = tools.execute(tmp_path, "bash", {"cwd": "..", "command": "pwd"})
    assert escaped.startswith("error:")


def test_terminal_read_empty(tmp_path: Path) -> None:
    tools = default_registry()
    assert tools.execute(tmp_path, "terminal_read", {}) == "(empty terminal log)"
