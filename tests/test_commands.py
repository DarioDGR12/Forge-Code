# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.commands import expand_command, load_commands


def test_load_and_expand_commands(tmp_path: Path) -> None:
    folder = tmp_path / ".forge" / "commands"
    folder.mkdir(parents=True)
    (folder / "explain.md").write_text(
        "# explain\nLook at $ARGS and summarize.\n", encoding="utf-8"
    )
    (folder / "help.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "find.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "pin.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "new.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "copy.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "files.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "set.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "api.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "chat.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "menu.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "contribute.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "contributions.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "lang.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "language.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "context.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "terminal.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "journal.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "open.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "why.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "note.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "tree.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "peek.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "turn.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "grep.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "ls.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "cat.md").write_text("should be ignored\n", encoding="utf-8")
    (folder / "Bad Name.md").write_text("invalid\n", encoding="utf-8")
    found = load_commands(tmp_path)
    assert list(found) == ["explain"]
    assert found["explain"].title == "explain"
    assert "auth" in expand_command(found["explain"], "auth")


def test_expand_appends_when_no_placeholder() -> None:
    from forge_code.commands import CustomCommand

    cmd = CustomCommand(name="n", body="Review the diff.", title="n")
    assert expand_command(cmd, "focus tests").endswith("focus tests")
    assert expand_command(cmd, "") == "Review the diff."
