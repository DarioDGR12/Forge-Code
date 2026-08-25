# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.prompts import system_prompt
from forge_code.tools.memory import memory_read, memory_write
from forge_code.tools.registry import default_registry


def test_memory_append_and_prompt(tmp_path: Path) -> None:
    assert memory_read(tmp_path, {}) == "(empty memory)"
    assert memory_write(tmp_path, {"note": ""}).startswith("error:")
    assert "flag" in memory_write(tmp_path, {"note": "--sneak"})
    wrote = memory_write(tmp_path, {"note": "we use pytest"})
    assert "remembered" in wrote
    text = memory_read(tmp_path, {})
    assert "we use pytest" in text
    prompt = system_prompt(tmp_path, "build")
    assert "Persistent memory" in prompt
    assert "we use pytest" in prompt


def test_memory_write_in_plan_mode(tmp_path: Path) -> None:
    tools = default_registry()
    result = tools.execute(
        tmp_path, "memory_write", {"note": "x"}, mode="plan"
    )
    assert "read-only" in result
    assert not (tmp_path / ".forge" / "memory.md").exists()
