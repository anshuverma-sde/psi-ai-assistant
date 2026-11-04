import asyncio
import logging

import groq
from groq import AsyncGroq

from app.core.utils.retry import retry_async
from app.infra.llm.base import ChatMessage, LLMUnavailableError

logger = logging.getLogger(__name__)

_RETRYABLE = (groq.APIConnectionError, groq.APITimeoutError, groq.InternalServerError)


_MAX_RATE_LIMIT_WAIT_S = 12.0


def _retry_after(exc: groq.RateLimitError) -> float | None:
    """Seconds Groq asks us to wait (free tier limits are per minute, so waits are usually short)."""
    try:
        return float(exc.response.headers.get("retry-after", ""))
    except (AttributeError, TypeError, ValueError):
        return None


def _failed_generation(exc: groq.BadRequestError) -> str | None:
    """Groq returns the raw generation when its JSON-mode validation fails."""
    body = exc.body if isinstance(exc.body, dict) else {}
    error = body.get("error", body)
    return error.get("failed_generation") if isinstance(error, dict) else None


class GroqProvider:
    """Groq free-tier models. Each model has its own quota, so on a rate limit we move down the list."""

    name = "groq"

    def __init__(self, api_key: str | None, model: str, fallback_models: list[str],
                 timeout_s: float, max_retries: int, reasoning_effort: str = "low") -> None:
        self.models = [model, *[m for m in fallback_models if m and m != model]]
        self.reasoning_effort = reasoning_effort
        self.max_retries = max_retries
        self._client = AsyncGroq(api_key=api_key or "missing", timeout=timeout_s, max_retries=0)
        self._configured = bool(api_key)

    async def _call(self, model: str, messages: list[ChatMessage], json_mode: bool,
                    temperature: float, max_tokens: int) -> str:
        kwargs: dict = {"response_format": {"type": "json_object"}} if json_mode else {}
        if model.startswith("openai/gpt-oss"):
            # Reasoning models: keep reasoning short and out of the message content.
            # Reasoning tokens count toward the completion budget, so leave headroom.
            kwargs["reasoning_effort"] = self.reasoning_effort
            kwargs["extra_body"] = {"include_reasoning": False}
            max_tokens += 600
        elif model.startswith("qwen/qwen3"):
            # Qwen 3 can think before answering; keep that out of the content we parse.
            kwargs["extra_body"] = {"reasoning_format": "hidden"}
            max_tokens += 600
        resp = await self._client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return resp.choices[0].message.content or ""

    async def complete(self, messages: list[ChatMessage], *, json_mode: bool = False,
                       temperature: float = 0.0, max_tokens: int = 1500) -> str:
        if not self._configured:
            raise LLMUnavailableError("GROQ_API_KEY is not configured")

        last_error: Exception | None = None
        for model in self.models:
            try:
                content = await self._call_with_rate_limit_wait(model, messages, json_mode, temperature, max_tokens)
                if model != self.models[0]:
                    logger.info("Answered by fallback model %s", model)
                return content
            except groq.RateLimitError as exc:
                logger.warning("Groq rate limit on %s, trying fallback model", model)
                last_error = exc
            except groq.NotFoundError as exc:
                logger.error("Groq model %s unavailable: %s", model, exc)
                last_error = exc
            except groq.BadRequestError as exc:
                # json_mode can fail validation on Groq's side; let the caller's repair loop handle it.
                generation = _failed_generation(exc) if json_mode else None
                if generation:
                    return generation
                raise LLMUnavailableError(f"Groq rejected the request: {exc}") from exc
            except (groq.APIError, *_RETRYABLE) as exc:
                last_error = exc
                break
        raise LLMUnavailableError(str(last_error))

    async def _call_with_rate_limit_wait(self, model: str, messages: list[ChatMessage], json_mode: bool,
                                         temperature: float, max_tokens: int) -> str:
        """Retries transient errors; on a 429 waits once if Groq's retry-after is short, else re-raises."""
        for attempt in range(2):
            try:
                return await retry_async(
                    lambda: self._call(model, messages, json_mode, temperature, max_tokens),
                    attempts=self.max_retries + 1,
                    retry_on=_RETRYABLE,
                    label=f"groq:{model}",
                )
            except groq.RateLimitError as exc:
                wait = _retry_after(exc)
                if attempt == 1 or wait is None or wait > _MAX_RATE_LIMIT_WAIT_S:
                    raise
                logger.info("Groq rate limit on %s — waiting %.1fs (retry-after)", model, wait)
                await asyncio.sleep(wait + 0.2)
        raise RuntimeError("unreachable")  # pragma: no cover
