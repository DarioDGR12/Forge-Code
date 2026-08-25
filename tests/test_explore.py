# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.models import Completion, Message
from forge_code.tools.explore import explore_repo, explore_with_complete


def test_explore_requires_question(tmp_path: Path) -> None:
    assert explore_repo(tmp_path, {}).startswith("error:")


def test_explore_with_complete(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    seen = {"tools": None}

    def fake_complete(_cfg, _messages, tools):
        seen["tools"] = tools
        return Completion(
            message=Message(role="assistant", content="add lives in app.py"),
            finish="stop",
        )

    text = explore_with_complete(tmp_path, "where is add?", fake_complete)
    assert "app.py" in text
    names = [item["function"]["name"] for item in seen["tools"] or []]
    assert "explore" not in names
    assert "write_file" not in names
