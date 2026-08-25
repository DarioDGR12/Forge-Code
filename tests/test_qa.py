# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.qa.runner import detect_checks, run_qa


def test_detects_pytest_example() -> None:
    root = Path(__file__).resolve().parents[1] / "examples" / "broken-add"
    names = [name for name, _ in detect_checks(root)]
    assert "pytest" in names


def test_broken_add_fails_qa() -> None:
    root = Path(__file__).resolve().parents[1] / "examples" / "broken-add"
    report = run_qa(root, timeout=60)
    assert report.ok is False
    assert any(item.name == "pytest" and item.passed is False for item in report.results)


def test_passing_python_qa(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\nversion='0'\n", encoding="utf-8")
    (tmp_path / "ok.py").write_text("VALUE = 1\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_ok.py").write_text("def test_ok():\n    assert 1 == 1\n", encoding="utf-8")
    report = run_qa(tmp_path, timeout=60)
    assert report.ok
