from app.core.config import Settings
from app.infra.llm.base import LLMProvider


def create_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "ollama":
        from app.infra.llm.ollama_provider import OllamaProvider

        return OllamaProvider(settings.ollama_base_url, settings.ollama_model,
                              settings.llm_timeout_s, settings.llm_max_retries)

    from app.infra.llm.groq_provider import GroqProvider

    return GroqProvider(
        api_key=settings.groq_api_key,
        model=settings.llm_model,
        fallback_models=settings.llm_fallback_model_list,
        timeout_s=settings.llm_timeout_s,
        max_retries=settings.llm_max_retries,
        reasoning_effort=settings.llm_reasoning_effort,
    )
