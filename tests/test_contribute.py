# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from urllib.parse import unquote

import pytest

from forge_code.contribute import (
    FEEDBACK_EMAIL,
    GITHUB_REPO,
    contribute_guide,
    mailto_url,
    open_github,
    save_recommendation,
    send_recommendation,
)


def test_mailto_targets_owner_email() -> None:
    url = mailto_url("Forge recommendation from Ada", "please add vim keys")
    assert url.startswith(f"mailto:{FEEDBACK_EMAIL}?")
    decoded = unquote(url)
    assert "please add vim keys" in decoded
    assert "Forge recommendation from Ada" in decoded


def test_save_and_send_recommendation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    urls: list[str] = []
    path, opened = send_recommendation(
        "add a dark theme",
        "Ada",
        open_url=lambda url: urls.append(url) or True,
    )
    assert opened is True
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Ada" in text
    assert "add a dark theme" in text
    assert FEEDBACK_EMAIL in text
    assert urls[0].startswith(f"mailto:{FEEDBACK_EMAIL}?")
    assert "add a dark theme" in unquote(urls[0])


def test_empty_recommendation_is_rejected(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    urls: list[str] = []
    with pytest.raises(ValueError):
        send_recommendation("   ", open_url=lambda url: urls.append(url) or True)
    assert urls == []
    assert list((tmp_path / "forge-code" / "contributions").glob("*.md")) == []


def test_save_survives_open_failure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    def boom(_url: str) -> bool:
        raise OSError("no mailer")

    path, opened = send_recommendation("keep this", "Ada", open_url=boom)
    assert opened is False
    assert path.exists()
    assert "keep this" in path.read_text(encoding="utf-8")


def test_contribute_guide_and_github() -> None:
    guide = contribute_guide()
    assert GITHUB_REPO in guide
    assert "git clone" in guide
    assert FEEDBACK_EMAIL in guide
    urls: list[str] = []
    assert open_github(open_url=lambda url: urls.append(url) or True) == GITHUB_REPO
    assert urls == [GITHUB_REPO]


def test_save_recommendation_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    path = save_recommendation("ship a TUI", "Dario")
    assert path.parent.name == "contributions"
    assert path.read_text(encoding="utf-8").startswith("# Forge recommendation")
