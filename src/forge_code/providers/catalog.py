# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

"""Built-in model vendors. New vendors belong here, not in the kernel."""

from __future__ import annotations

DEFAULT_PROVIDERS: dict[str, dict[str, str]] = {
    "openai": {
        "kind": "openai",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4.1-mini",
        "key_env": "OPENAI_API_KEY",
    },
    "anthropic": {
        "kind": "anthropic",
        "base_url": "https://api.anthropic.com",
        "default_model": "claude-sonnet-4-20250514",
        "key_env": "ANTHROPIC_API_KEY",
    },
    "openrouter": {
        "kind": "openai",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "anthropic/claude-sonnet-4",
        "key_env": "OPENROUTER_API_KEY",
    },
    "groq": {
        "kind": "openai",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "key_env": "GROQ_API_KEY",
    },
    "mistral": {
        "kind": "openai",
        "base_url": "https://api.mistral.ai/v1",
        "default_model": "codestral-latest",
        "key_env": "MISTRAL_API_KEY",
    },
    "deepseek": {
        "kind": "openai",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "key_env": "DEEPSEEK_API_KEY",
    },
    "kimi": {
        "kind": "openai",
        "base_url": "https://api.moonshot.ai/v1",
        "default_model": "kimi-k2-turbo-preview",
        "key_env": "MOONSHOT_API_KEY",
    },
    "gemini": {
        "kind": "openai",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_model": "gemini-2.5-flash",
        "key_env": "GEMINI_API_KEY",
    },
    "xai": {
        "kind": "openai",
        "base_url": "https://api.x.ai/v1",
        "default_model": "grok-3-mini",
        "key_env": "XAI_API_KEY",
    },
    "together": {
        "kind": "openai",
        "base_url": "https://api.together.xyz/v1",
        "default_model": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "key_env": "TOGETHER_API_KEY",
    },
    "fireworks": {
        "kind": "openai",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "default_model": "accounts/fireworks/models/llama-v3p3-70b-instruct",
        "key_env": "FIREWORKS_API_KEY",
    },
    "cerebras": {
        "kind": "openai",
        "base_url": "https://api.cerebras.ai/v1",
        "default_model": "llama-3.3-70b",
        "key_env": "CEREBRAS_API_KEY",
    },
    "perplexity": {
        "kind": "openai",
        "base_url": "https://api.perplexity.ai",
        "default_model": "sonar-pro",
        "key_env": "PERPLEXITY_API_KEY",
    },
    "cohere": {
        "kind": "openai",
        "base_url": "https://api.cohere.ai/compatibility/v1",
        "default_model": "command-a-03-2025",
        "key_env": "COHERE_API_KEY",
    },
    "hf": {
        "kind": "openai",
        "base_url": "https://router.huggingface.co/v1",
        "default_model": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "key_env": "HF_TOKEN",
    },
    "nvidia": {
        "kind": "openai",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "default_model": "meta/llama-3.3-70b-instruct",
        "key_env": "NVIDIA_API_KEY",
    },
    "dashscope": {
        "kind": "openai",
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
        "key_env": "DASHSCOPE_API_KEY",
    },
    "glm": {
        "kind": "openai",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4.5",
        "key_env": "ZHIPUAI_API_KEY",
    },
    "minimax": {
        "kind": "openai",
        "base_url": "https://api.minimax.io/v1",
        "default_model": "MiniMax-M2",
        "key_env": "MINIMAX_API_KEY",
    },
    "siliconflow": {
        "kind": "openai",
        "base_url": "https://api.siliconflow.cn/v1",
        "default_model": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "key_env": "SILICONFLOW_API_KEY",
    },
    "deepinfra": {
        "kind": "openai",
        "base_url": "https://api.deepinfra.com/v1/openai",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct",
        "key_env": "DEEPINFRA_API_KEY",
    },
    "sambanova": {
        "kind": "openai",
        "base_url": "https://api.sambanova.ai/v1",
        "default_model": "Meta-Llama-3.3-70B-Instruct",
        "key_env": "SAMBANOVA_API_KEY",
    },
    "github": {
        "kind": "openai",
        "base_url": "https://models.github.ai/inference",
        "default_model": "openai/gpt-4.1-mini",
        "key_env": "GITHUB_TOKEN",
    },
    "novita": {
        "kind": "openai",
        "base_url": "https://api.novita.ai/v3/openai",
        "default_model": "deepseek/deepseek-v3.1",
        "key_env": "NOVITA_API_KEY",
    },
    "ark": {
        "kind": "openai",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "default_model": "doubao-pro-32k",
        "key_env": "ARK_API_KEY",
    },
    "yi": {
        "kind": "openai",
        "base_url": "https://api.lingyiwanwu.com/v1",
        "default_model": "yi-lightning",
        "key_env": "YI_API_KEY",
    },
    "ollama": {
        "kind": "openai",
        "base_url": "http://127.0.0.1:11434/v1",
        "default_model": "qwen2.5-coder:7b",
        "key_env": "OLLAMA_API_KEY",
        "local": "true",
    },
    "llamacpp": {
        "kind": "openai",
        "base_url": "http://127.0.0.1:8080/v1",
        "default_model": "local",
        "key_env": "LLAMACPP_API_KEY",
        "local": "true",
    },
    "lmstudio": {
        "kind": "openai",
        "base_url": "http://127.0.0.1:1234/v1",
        "default_model": "local",
        "key_env": "LMSTUDIO_API_KEY",
        "local": "true",
    },
    "custom": {
        "kind": "openai",
        "base_url": "http://127.0.0.1:8000/v1",
        "default_model": "local",
        "key_env": "FORGE_API_KEY",
        "local": "true",
    },
}

PROVIDER_ALIASES: dict[str, str] = {
    "chatgpt": "openai",
    "claude": "anthropic",
    "mistralai": "mistral",
    "mistral-ai": "mistral",
    "codestral": "mistral",
    "deep-seek": "deepseek",
    "moonshot": "kimi",
    "moonshot-ai": "kimi",
    "k2": "kimi",
    "google": "gemini",
    "google-ai": "gemini",
    "googleai": "gemini",
    "grok": "xai",
    "x-ai": "xai",
    "together-ai": "together",
    "togetherai": "together",
    "fireworks-ai": "fireworks",
    "pplx": "perplexity",
    "perplexity-ai": "perplexity",
    "huggingface": "hf",
    "huggingface-hub": "hf",
    "nim": "nvidia",
    "nvidia-nim": "nvidia",
    "qwen": "dashscope",
    "alibaba": "dashscope",
    "aliyun": "dashscope",
    "tongyi": "dashscope",
    "zhipu": "glm",
    "zhipuai": "glm",
    "zai": "glm",
    "z-ai": "glm",
    "bigmodel": "glm",
    "doubao": "ark",
    "volc": "ark",
    "volcengine": "ark",
    "byteplus": "ark",
    "01ai": "yi",
    "01-ai": "yi",
    "lingyi": "yi",
    "github-models": "github",
    "lm-studio": "lmstudio",
    "llama.cpp": "llamacpp",
    "llama-cpp": "llamacpp",
    "silicon": "siliconflow",
}


def resolve_provider(name: str) -> str:
    raw = (name or "").strip().lower().replace("_", "-")
    if not raw:
        raise KeyError("provider name required")
    if raw in DEFAULT_PROVIDERS:
        return raw
    if raw in PROVIDER_ALIASES:
        return PROVIDER_ALIASES[raw]
    collapsed = raw.replace("-", "")
    for key in DEFAULT_PROVIDERS:
        if key.replace("-", "") == collapsed:
            return key
    for alias, canonical in PROVIDER_ALIASES.items():
        if alias.replace("-", "") == collapsed:
            return canonical
    known = ", ".join(sorted(DEFAULT_PROVIDERS))
    raise KeyError(f"unknown provider {name!r}. known: {known}")


def aliases_for(canonical: str) -> list[str]:
    return sorted(alias for alias, name in PROVIDER_ALIASES.items() if name == canonical)


def is_local(spec: dict[str, str]) -> bool:
    return spec.get("local") == "true"
