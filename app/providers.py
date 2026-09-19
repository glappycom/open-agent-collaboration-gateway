from dataclasses import dataclass
from time import perf_counter

from .config import settings
from .schemas import Provider


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProviderConfig:
    name: Provider
    model: str
    base_url: str | None
    configured: bool


@dataclass(frozen=True)
class CallResult:
    text: str
    model: str
    latency_ms: int


def provider_configs() -> list[ProviderConfig]:
    return [
        ProviderConfig(
            name=Provider.openai,
            model=settings.openai_model,
            base_url=None,
            configured=bool(settings.openai_api_key),
        ),
        ProviderConfig(
            name=Provider.grok,
            model=settings.xai_model,
            base_url="https://api.x.ai/v1",
            configured=bool(settings.xai_api_key),
        ),
    ]


def _client(provider: Provider):
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ProviderError(
            "The 'openai' package is required at runtime. Install dependencies with: pip install -r requirements.txt"
        ) from exc

    if provider == Provider.openai:
        if not settings.openai_api_key:
            raise ProviderError("OPENAI_API_KEY is not configured")
        return OpenAI(api_key=settings.openai_api_key), settings.openai_model

    if not settings.xai_api_key:
        raise ProviderError("XAI_API_KEY is not configured")
    return OpenAI(api_key=settings.xai_api_key, base_url="https://api.x.ai/v1"), settings.xai_model


def call_model(provider: Provider, prompt: str, system_context: str | None = None) -> CallResult:
    client, model = _client(provider)
    input_items = []
    if system_context:
        input_items.append({"role": "system", "content": system_context})
    input_items.append({"role": "user", "content": prompt})

    started = perf_counter()
    try:
        response = client.responses.create(
            model=model,
            input=input_items,
            store=settings.provider_store_responses,
        )
        text = getattr(response, "output_text", None)
        rendered = text.strip() if text else str(response)
        return CallResult(
            text=rendered,
            model=getattr(response, "model", None) or model,
            latency_ms=round((perf_counter() - started) * 1000),
        )
    except Exception as exc:
        raise ProviderError(f"{provider.value} request failed: {exc}") from exc
