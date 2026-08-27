# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from forge_code.providers.catalog import DEFAULT_PROVIDERS, resolve_provider


def test_resolve_aliases() -> None:
    assert resolve_provider("mistralai") == "mistral"
    assert resolve_provider("Mistral-AI") == "mistral"
    assert resolve_provider("deepseek") == "deepseek"
    assert resolve_provider("moonshot") == "kimi"
    assert resolve_provider("kimi") == "kimi"
    assert resolve_provider("google") == "gemini"
    assert resolve_provider("grok") == "xai"
    assert resolve_provider("claude") == "anthropic"
    assert resolve_provider("chatgpt") == "openai"
    assert resolve_provider("qwen") == "dashscope"
    assert resolve_provider("zhipu") == "glm"
    assert resolve_provider("lm-studio") == "lmstudio"
    assert "mistral" in DEFAULT_PROVIDERS
    assert "deepseek" in DEFAULT_PROVIDERS
    assert "kimi" in DEFAULT_PROVIDERS
    try:
        resolve_provider("no-such-vendor")
    except KeyError:
        pass
    else:
        raise AssertionError("unknown provider should raise")
