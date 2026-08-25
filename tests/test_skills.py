# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.prompts import system_prompt
from forge_code.skills import load_skills


def test_load_skills_empty(tmp_path: Path) -> None:
    assert load_skills(tmp_path) == ""


def test_skills_in_system_prompt(tmp_path: Path) -> None:
    folder = tmp_path / ".forge" / "skills"
    folder.mkdir(parents=True)
    (folder / "python.md").write_text("Prefer pytest. No new deps.\n", encoding="utf-8")
    assert "Prefer pytest" in load_skills(tmp_path)
    prompt = system_prompt(tmp_path, "build")
    assert "Project skills" in prompt
    assert "Prefer pytest" in prompt
