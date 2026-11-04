import json
import re
from dataclasses import dataclass
from typing import Any, Literal, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str


class LLMUnavailableError(Exception):
    """Provider down, timed out or rate-limited after retries."""


class LLMOutputError(Exception):
    """Provider answered but the output could not be parsed/validated."""


class LLMProvider(Protocol):
    name: str

    async def complete(
        self, messages: list[ChatMessage], *, json_mode: bool = False, temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> str: ...


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_json_object(raw: str) -> dict[str, Any]:
    text = _FENCE.sub("", raw.strip())
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise LLMOutputError("No JSON object in model output")
    try:
        value = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMOutputError(f"Invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise LLMOutputError("Model output is not a JSON object")
    return value


async def complete_structured(
    llm: LLMProvider,
    messages: list[ChatMessage],
    schema: type[T],
    *,
    repair_attempts: int = 1,
    max_tokens: int = 1500,
) -> T:
    """Ask for JSON, validate with Pydantic, and give the model one chance to repair errors."""
    convo = list(messages)
    for attempt in range(repair_attempts + 1):
        raw = await llm.complete(convo, json_mode=True, max_tokens=max_tokens)
        try:
            return schema.model_validate(parse_json_object(raw))
        except (LLMOutputError, ValidationError) as exc:
            if attempt == repair_attempts:
                raise LLMOutputError(str(exc)) from exc
            convo = [
                *messages,
                ChatMessage("assistant", raw),
                ChatMessage(
                    "user",
                    f"Your JSON did not match the required schema: {str(exc)[:800]}\n"
                    "Return ONLY the corrected JSON object.",
                ),
            ]
    raise LLMOutputError("unreachable")  # pragma: no cover
