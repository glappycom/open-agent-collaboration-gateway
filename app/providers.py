from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .config import settings
from .schemas import Provider


class ProviderError(RuntimeError):
    pass


class ProviderConfigurationError(ProviderError):
    pass


class ProviderResponseError(ProviderError):
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
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class _NormalizedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    model: str = Field(min_length=1)
    latency_ms: int = Field(ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class ProviderAdapter(Protocol):
    @property
    def provider(self) -> Provider: ...

    @property
    def model(self) -> str: ...

    @property
    def base_url(self) -> str | None: ...

    @property
    def configured(self) -> bool: ...

    def invoke(self, prompt: str, system_context: str | None = None) -> CallResult: ...


@dataclass
class OpenAICompatibleAdapter:
    provider: Provider
    model: str
    api_key: str
    base_url: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _client(self):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderConfigurationError(
                "The 'openai' package is required at runtime. Install dependencies with: pip install -r requirements.txt"
            ) from exc

        if not self.api_key:
            variable = "OPENAI_API_KEY" if self.provider == Provider.openai else "XAI_API_KEY"
            raise ProviderConfigurationError(f"{variable} is not configured")

        kwargs = {
            "api_key": self.api_key,
            "timeout": settings.provider_timeout_seconds,
            "max_retries": 0,
        }
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return OpenAI(**kwargs)

    def _input_items(self, prompt: str, system_context: str | None) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        if system_context:
            items.append({"role": "system", "content": system_context})
        items.append({"role": "user", "content": prompt})
        return items

    def _extract_usage(self, response) -> tuple[int | None, int | None, int | None]:
        usage = getattr(response, "usage", None)
        if usage is None:
            return None, None, None

        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)

        if total_tokens is None and input_tokens is not None and output_tokens is not None:
            total_tokens = input_tokens + output_tokens

        return input_tokens, output_tokens, total_tokens

    def _validate_text(self, value: object) -> str:
        if not isinstance(value, str):
            raise ProviderResponseError(
                f"{self.provider.value} returned no textual output"
            )

        text = value.strip()
        if not text:
            raise ProviderResponseError(
                f"{self.provider.value} returned empty textual output"
            )

        if len(text) > settings.max_provider_output_chars:
            raise ProviderResponseError(
                f"{self.provider.value} output exceeds MAX_PROVIDER_OUTPUT_CHARS "
                f"({settings.max_provider_output_chars})"
            )

        if self.api_key and self.api_key in text:
            raise ProviderResponseError(
                f"{self.provider.value} output contained configured provider credentials"
            )

        return text

    def invoke(self, prompt: str, system_context: str | None = None) -> CallResult:
        client = self._client()
        started = perf_counter()

        try:
            response = client.responses.create(
                model=self.model,
                input=self._input_items(prompt, system_context),
                store=settings.provider_store_responses,
            )
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"{self.provider.value} request failed: {exc}") from exc

        latency_ms = round((perf_counter() - started) * 1000)
        text = self._validate_text(getattr(response, "output_text", None))
        response_model = getattr(response, "model", None) or self.model
        input_tokens, output_tokens, total_tokens = self._extract_usage(response)

        try:
            normalized = _NormalizedResponse(
                text=text,
                model=response_model,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
            )
        except ValidationError as exc:
            raise ProviderResponseError(
                f"{self.provider.value} returned invalid normalized response metadata"
            ) from exc

        return CallResult(**normalized.model_dump())


def _adapters() -> dict[Provider, ProviderAdapter]:
    return {
        Provider.openai: OpenAICompatibleAdapter(
            provider=Provider.openai,
            model=settings.openai_model,
            api_key=settings.openai_api_key,
        ),
        Provider.grok: OpenAICompatibleAdapter(
            provider=Provider.grok,
            model=settings.xai_model,
            api_key=settings.xai_api_key,
            base_url="https://api.x.ai/v1",
        ),
    }


def get_adapter(provider: Provider) -> ProviderAdapter:
    adapters = _adapters()
    try:
        return adapters[provider]
    except KeyError as exc:
        raise ProviderConfigurationError(
            f"no provider adapter is registered for '{provider.value}'"
        ) from exc


def provider_configs() -> list[ProviderConfig]:
    configs: list[ProviderConfig] = []
    for adapter in _adapters().values():
        configs.append(
            ProviderConfig(
                name=adapter.provider,
                model=adapter.model,
                base_url=adapter.base_url,
                configured=adapter.configured,
            )
        )
    return configs


def call_model(provider: Provider, prompt: str, system_context: str | None = None) -> CallResult:
    return get_adapter(provider).invoke(prompt, system_context)
