# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.scaffold import init_workspace


def test_init_writes_then_skips(tmp_path: Path) -> None:
    first = dict(init_workspace(tmp_path))
    assert first["AGENTS.md"] == "wrote"
    assert first[".forge/commands/explain.md"] == "wrote"
    assert first[".forge/commands/test.md"] == "wrote"
    assert first[".forge/commands/commit-msg.md"] == "wrote"
    assert first[".forge/skills/python.md"] == "wrote"
    assert first[".forge/context.md"] == "wrote"
    assert (tmp_path / ".forge" / "context.md").is_file()
    assert (tmp_path / "AGENTS.md").is_file()
    second = dict(init_workspace(tmp_path))
    assert set(second.values()) == {"exists"}
    assert (tmp_path / ".forgeignore").read_text(encoding="utf-8").startswith("#")
