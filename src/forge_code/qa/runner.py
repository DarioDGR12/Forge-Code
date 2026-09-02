# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class QAResult:
    name: str
    command: str
    passed: bool
    output: str
    duration_ms: int


@dataclass
class QAReport:
    ok: bool
    results: list[QAResult] = field(default_factory=list)

    def summary(self) -> str:
        if not self.results:
            return "QA: no checks detected in this repo."
        lines = ["QA: " + ("passed" if self.ok else "failed")]
        for item in self.results:
            mark = "pass" if item.passed else "fail"
            lines.append(f"  - {item.name}: {mark} ({item.duration_ms}ms)")
            if not item.passed and item.output:
                lines.append(item.output[-4000:])
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {"ok": self.ok, "results": [asdict(item) for item in self.results]}

    @classmethod
    def from_dict(cls, raw: dict) -> "QAReport":
        results = []
        for item in raw.get("results") or []:
            if not isinstance(item, dict):
                continue
            results.append(
                QAResult(
                    name=str(item.get("name") or ""),
                    command=str(item.get("command") or ""),
                    passed=bool(item.get("passed")),
                    output=str(item.get("output") or ""),
                    duration_ms=int(item.get("duration_ms") or 0),
                )
            )
        return cls(ok=bool(raw.get("ok")), results=results)


LAST_QA_REL = Path(".forge") / "last-qa.json"


def save_last_qa(root: Path, report: QAReport) -> Path:
    path = root / LAST_QA_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def load_last_qa(root: Path) -> QAReport | None:
    path = root / LAST_QA_REL
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    return QAReport.from_dict(raw)


def detect_checks(root: Path) -> list[tuple[str, list[str]]]:
    checks: list[tuple[str, list[str]]] = []
    if (root / "pyproject.toml").exists() or (root / "pytest.ini").exists() or any(
        root.glob("tests/test_*.py")
    ):
        checks.append(
            (
                "pytest",
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "--rootdir",
                    ".",
                    "-o",
                    "testpaths=",
                    "-o",
                    "addopts=",
                ],
            )
        )
    elif any(root.glob("test_*.py")) or any(root.glob("tests/*.py")):
        checks.append(("unittest", [sys.executable, "-m", "unittest", "discover", "-q"]))
    if (root / "package.json").exists():
        try:
            pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pkg = {}
        scripts = pkg.get("scripts") or {}
        if "test" in scripts:
            checks.append(("npm test", ["npm", "test", "--silent"]))
        if "lint" in scripts:
            checks.append(("npm lint", ["npm", "run", "lint", "--silent"]))
    if (root / "Cargo.toml").exists():
        checks.append(("cargo test", ["cargo", "test", "--quiet"]))
    if (root / "go.mod").exists():
        checks.append(("go test", ["go", "test", "./..."]))
    if (root / "pyproject.toml").exists() or any(root.glob("*.py")):
        compile_cmd = [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "-x",
            r"(^|[\\/])(\.venv|__pycache__|\.git)([\\/]|$)",
            ".",
        ]
        if not any(name == "pytest" for name, _ in checks):
            checks.append(("compileall", compile_cmd))
    if (root / "ruff.toml").exists() or (root / ".ruff.toml").exists():
        checks.append(("ruff", ["ruff", "check", "."]))
    if (root / "mypy.ini").exists() or (root / "pyproject.toml").exists() and _pyproject_has(root, "mypy"):
        checks.append(("mypy", ["mypy", "."]))
    if (root / "Makefile").exists():
        makefile = (root / "Makefile").read_text(encoding="utf-8", errors="replace")
        if "\ntest:" in f"\n{makefile}" or makefile.startswith("test:"):
            checks.append(("make test", ["make", "test"]))
    return checks


def _pyproject_has(root: Path, section: str) -> bool:
    text = (root / "pyproject.toml").read_text(encoding="utf-8", errors="replace")
    return f"[tool.{section}" in text


def run_qa(root: Path, timeout: int = 120, extra: list[str] | None = None) -> QAReport:
    checks = detect_checks(root)
    for command in extra or []:
        checks.append((command, command.split()))
    results: list[QAResult] = []
    for name, command in checks:
        started = time.perf_counter()
        try:
            env = {
                key: value
                for key, value in os.environ.items()
                if not key.startswith("PYTEST_")
            }
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            completed = subprocess.run(
                command,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=env,
            )
            output = (completed.stdout or "") + (completed.stderr or "")
            passed = completed.returncode == 0
        except FileNotFoundError:
            output = f"command not found: {command[0]}"
            passed = False
        except subprocess.TimeoutExpired:
            output = f"timed out after {timeout}s"
            passed = False
        results.append(
            QAResult(
                name=name,
                command=" ".join(command),
                passed=passed,
                output=output.strip(),
                duration_ms=int((time.perf_counter() - started) * 1000),
            )
        )
    ok = bool(results) and all(item.passed for item in results)
    if not results:
        ok = True
    return QAReport(ok=ok, results=results)
