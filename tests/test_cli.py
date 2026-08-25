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
