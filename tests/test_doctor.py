# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.config import AppConfig
from forge_code.doctor import doctor_lines


def test_doctor_lines_missing_key_and_local(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("FORGE_API_KEY", raising=False)
    monkeypatch.setattr(
        "forge_code.doctor.probe_local",
        lambda: {"ollama": ["qwen2.5-coder"], "llamacpp": []},
    )
    lines = "\n".join(doctor_lines(tmp_path, AppConfig()))
    assert "missing" in lines
    assert "qwen2.5-coder" in lines
    assert "down" in lines
    local = AppConfig(provider="ollama", model="local")
    assert "local" in "\n".join(doctor_lines(tmp_path, local))
