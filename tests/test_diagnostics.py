# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.diagnostics import format_diagnostics, run_diagnostics


def test_no_paths_is_empty(tmp_path: Path) -> None:
    assert run_diagnostics(tmp_path, []) == []
    assert "no diagnostics" in format_diagnostics([])
