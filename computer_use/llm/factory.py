"""Factories for creating provider-aware LLM clients."""

from __future__ import annotations

from . import openai_adapter
from .providers import get_provider_profile


def create_llm_client(
    *,
    provider: str,
    api_key: str,
    base_url: str,
    provider_config: dict | None = None,
) -> openai_adapter.OpenAiChatClient:
    """Create an LLM client for the configured provider."""
    if openai_adapter.OpenAI is None:
        raise ImportError('openai 未安装，请先执行 pip install -r requirements.txt')

    provider_profile = get_provider_profile(provider)

    sdk_client = openai_adapter.OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    return openai_adapter.OpenAiChatClient(
        sdk_client=sdk_client,
        provider=provider_profile.name,
        provider_profile=provider_profile,
        provider_config=provider_config,
    )
