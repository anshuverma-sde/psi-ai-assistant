"""The provider walks down its model list when a model is rate-limited (each has its own quota)."""

import groq
import httpx
import pytest

from app.infra.llm.base import ChatMessage, LLMUnavailableError
from app.infra.llm.groq_provider import GroqProvider


def rate_limited(model: str) -> groq.RateLimitError:
    response = httpx.Response(429, headers={"retry-after": "600"},
                              request=httpx.Request("POST", "https://api.groq.com"))
    return groq.RateLimitError(f"daily limit reached for {model}", response=response, body=None)


def provider(exhausted: set[str]) -> tuple[GroqProvider, list[str]]:
    p = GroqProvider(api_key="test", model="big", fallback_models=["small", "qwen", "big"], timeout_s=5, max_retries=0)
    calls: list[str] = []

    async def fake_call(model, *_args):
        calls.append(model)
        if model in exhausted:
            raise rate_limited(model)
        return f"answer from {model}"

    p._call = fake_call  # type: ignore[method-assign]
    return p, calls


async def test_falls_through_models_in_order():
    p, calls = provider(exhausted={"big", "small"})
    assert p.models == ["big", "small", "qwen"]  # duplicates of the primary are dropped
    assert await p.complete([ChatMessage("user", "hi")]) == "answer from qwen"
    assert calls == ["big", "small", "qwen"]  # long retry-after → no waiting, move on


async def test_all_models_exhausted_raises_unavailable():
    p, _ = provider(exhausted={"big", "small", "qwen"})
    with pytest.raises(LLMUnavailableError):
        await p.complete([ChatMessage("user", "hi")])
