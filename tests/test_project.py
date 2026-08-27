# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

import os
import time
from pathlib import Path

from forge_code.project import ensure_context, load_context, project_map, render_context, save_context
from forge_code.prompts import system_prompt
from forge_code.tools.registry import default_registry


def test_project_map_writes_context(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo app\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    text = render_context(tmp_path)
    assert "python" in text
    assert "Demo app" in text
    assert "src/" in text
    path = save_context(tmp_path)
    assert path.is_file()
    assert "Forge project context" in load_context(tmp_path)
    prompt = system_prompt(tmp_path, "build")
    assert "Project context" in prompt
    assert "python" in prompt


def test_project_map_tool_and_plan_mode(tmp_path: Path) -> None:
    tools = default_registry()
    wrote = tools.execute(tmp_path, "project_map", {})
    assert "wrote" in wrote
    assert (tmp_path / ".forge" / "context.md").is_file()
    blocked = tools.execute(tmp_path, "project_map", {}, mode="plan")
    assert "read-only" in blocked
    names = tools.names()
    assert "project_map" in names
    assert "terminal_read" in names


def test_ensure_context_does_not_overwrite(tmp_path: Path) -> None:
    save_context(tmp_path)
    path = tmp_path / ".forge" / "context.md"
    path.write_text("# custom\n", encoding="utf-8")
    assert ensure_context(tmp_path).startswith("# custom")


def test_ensure_context_refreshes_when_marker_newer(tmp_path: Path) -> None:
    save_context(tmp_path)
    path = tmp_path / ".forge" / "context.md"
    path.write_text("# custom\n", encoding="utf-8")
    marker = tmp_path / "pyproject.toml"
    marker.write_text("[project]\nname='demo'\n", encoding="utf-8")
    now = time.time()
    os.utime(path, (now - 20, now - 20))
    os.utime(marker, (now, now))
    text = ensure_context(tmp_path)
    assert "python" in text
    assert "# custom" not in text


def test_context_includes_scripts_entry_and_languages(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project.scripts]\nforge = 'forge_code.cli:main'\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text("print(1)\n", encoding="utf-8")
    text = render_context(tmp_path)
    assert "forge (pyproject)" in text
    assert "main.py" in text
    assert ".py" in text


def test_nested_agents_and_shell_in_prompt(tmp_path: Path) -> None:
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "AGENTS.md").write_text("use pytest\n", encoding="utf-8")
    prompt = system_prompt(tmp_path, "build")
    assert "pkg/AGENTS.md" in prompt
    assert "use pytest" in prompt
    assert "Shell: cwd" in prompt
    assert "last_exit" in prompt
