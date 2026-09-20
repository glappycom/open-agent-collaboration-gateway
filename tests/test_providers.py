from types import SimpleNamespace

import pytest

from app import providers
from app.schemas import Provider


class FakeResponses:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, response):
        self.responses = FakeResponses(response)


def _adapter(api_key="test-provider-key"):
    return providers.OpenAICompatibleAdapter(
        provider=Provider.openai,
        model="test-model",
        api_key=api_key,
    )


def test_adapter_normalizes_valid_response(monkeypatch):
    response = SimpleNamespace(
        output_text="  useful answer  ",
        model="provider-model",
        usage=SimpleNamespace(input_tokens=10, output_tokens=5, total_tokens=15),
    )
    adapter = _adapter()
    client = FakeClient(response)
    monkeypatch.setattr(adapter, "_client", lambda: client)

    result = adapter.invoke("hello", "context")

    assert result.text == "useful answer"
    assert result.model == "provider-model"
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.total_tokens == 15
    assert client.responses.calls[0]["store"] == providers.settings.provider_store_responses


def test_adapter_rejects_empty_output(monkeypatch):
    adapter = _adapter()
    monkeypatch.setattr(
        adapter,
        "_client",
        lambda: FakeClient(SimpleNamespace(output_text="   ", model="test-model", usage=None)),
    )

    with pytest.raises(providers.ProviderResponseError):
        adapter.invoke("hello")


def test_adapter_rejects_missing_text(monkeypatch):
    adapter = _adapter()
    monkeypatch.setattr(
        adapter,
        "_client",
        lambda: FakeClient(SimpleNamespace(model="test-model", usage=None)),
    )

    with pytest.raises(providers.ProviderResponseError):
        adapter.invoke("hello")


def test_adapter_rejects_oversized_output(monkeypatch):
    adapter = _adapter()
    monkeypatch.setattr(providers.settings, "max_provider_output_chars", 10)
    monkeypatch.setattr(
        adapter,
        "_client",
        lambda: FakeClient(
            SimpleNamespace(output_text="x" * 11, model="test-model", usage=None)
        ),
    )

    with pytest.raises(providers.ProviderResponseError):
        adapter.invoke("hello")


def test_adapter_fails_closed_on_credential_leak(monkeypatch):
    key = "test-secret-provider-key"
    adapter = _adapter(api_key=key)
    monkeypatch.setattr(
        adapter,
        "_client",
        lambda: FakeClient(
            SimpleNamespace(
                output_text=f"accidental credential: {key}",
                model="test-model",
                usage=None,
            )
        ),
    )

    with pytest.raises(providers.ProviderResponseError):
        adapter.invoke("hello")


def test_adapter_does_not_use_sdk_retries(monkeypatch):
    captured = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setitem(__import__("sys").modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))

    adapter = _adapter()
    adapter._client()

    assert captured["max_retries"] == 0
    assert captured["timeout"] == providers.settings.provider_timeout_seconds
