import httpx

from app.core.utils.retry import retry_async
from app.infra.llm.base import ChatMessage, LLMUnavailableError


class OllamaProvider:
    """Optional fully-local provider (requires a running Ollama). Not used by default."""

    name = "ollama"

    def __init__(self, base_url: str, model: str, timeout_s: float, max_retries: int) -> None:
        self.model = model
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout_s)

    async def complete(self, messages: list[ChatMessage], *, json_mode: bool = False,
                       temperature: float = 0.0, max_tokens: int = 1500) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if json_mode:
            payload["format"] = "json"

        async def _call() -> str:
            resp = await self._client.post("/api/chat", json=payload)
            resp.raise_for_status()
            return resp.json()["message"]["content"]

        try:
            return await retry_async(_call, attempts=self.max_retries + 1,
                                     retry_on=(httpx.TransportError,), label="ollama")
        except (httpx.HTTPError, KeyError) as exc:
            raise LLMUnavailableError(str(exc)) from exc
