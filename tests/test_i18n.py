# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from forge_code.i18n import lang, t


def test_lang_and_spanish(monkeypatch) -> None:
    monkeypatch.setenv("FORGE_LANG", "es")
    monkeypatch.delenv("LANG", raising=False)
    assert lang() == "es"
    assert "forjando" in t("forging")
    assert "s/N" in t("allow_bash", cmd="ls")
    assert "nada" in t("no_diff")


def test_lang_english_default(monkeypatch) -> None:
    monkeypatch.delenv("FORGE_LANG", raising=False)
    monkeypatch.setenv("LANG", "en_US.UTF-8")
    assert lang() == "en"
    assert t("bye") == "bye"
