# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.permissions import PermissionConfig, PermissionGate
from forge_code.tools.registry import default_registry


def test_blocks_secret_writes(tmp_path: Path) -> None:
    gate = PermissionGate(tmp_path)
    tools = default_registry(gate)
    result = tools.execute(
        tmp_path, "write_file", {"path": ".env", "content": "SECRET=1"}, mode="build"
    )
    assert result.startswith("error:")
    assert not (tmp_path / ".env").exists()


def test_blocks_destructive_bash(tmp_path: Path) -> None:
    gate = PermissionGate(tmp_path)
    tools = default_registry(gate)
    result = tools.execute(tmp_path, "bash", {"command": "rm -rf /"}, mode="build")
    assert "destructive" in result


def test_bash_deny_policy(tmp_path: Path) -> None:
    gate = PermissionGate(tmp_path, PermissionConfig(bash="deny"))
    tools = default_registry(gate)
    result = tools.execute(tmp_path, "bash", {"command": "echo hi"}, mode="build")
    assert "disabled" in result


def test_bash_ask_denied_and_allowed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("FORGE_YES", raising=False)
    gate = PermissionGate(tmp_path, PermissionConfig(bash="ask"))
    denied = default_registry(gate, ask=lambda *_: False)
    assert "denied" in denied.execute(tmp_path, "bash", {"command": "echo hi"})

    allowed = default_registry(gate, ask=lambda *_: True)
    result = allowed.execute(tmp_path, "bash", {"command": "echo hi"})
    assert "exit 0" in result
    assert "hi" in result
