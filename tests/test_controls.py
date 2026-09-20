import pytest

from app import controls
from app.providers import CallResult, ProviderError
from app.schemas import Provider


def setup_function():
    controls.reset_circuit_breakers()
    controls.request_rate_limiter.reset()
    controls.cancellation_registry.reset()


def test_redact_text_masks_provider_secrets():
    value = "OPENAI_API_KEY=sk-abcdefghijklmnop and XAI_API_KEY=xai-abcdefghijklmnop"
    redacted = controls.redact_text(value)
    assert "sk-abcdefghijklmnop" not in redacted
    assert "xai-abcdefghijklmnop" not in redacted
    assert "[REDACTED]" in redacted


def test_controlled_call_retries_then_succeeds(monkeypatch):
    attempts = {"count": 0}

    def fake_call(provider, prompt, system_context=None):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ProviderError("temporary")
        return CallResult(text="ok", model="test", latency_ms=1)

    monkeypatch.setattr(controls, "call_model", fake_call)
    monkeypatch.setattr(controls.settings, "provider_max_retries", 2)
    monkeypatch.setattr(controls.settings, "provider_retry_backoff_seconds", 0)

    result = controls.controlled_call(Provider.openai, "hello")
    assert result.text == "ok"
    assert attempts["count"] == 3


def test_circuit_breaker_opens_after_threshold(monkeypatch):
    def always_fail(provider, prompt, system_context=None):
        raise ProviderError("down")

    monkeypatch.setattr(controls, "call_model", always_fail)
    monkeypatch.setattr(controls.settings, "provider_max_retries", 0)
    monkeypatch.setattr(controls.settings, "circuit_breaker_failures", 2)
    monkeypatch.setattr(controls.settings, "circuit_breaker_reset_seconds", 999)

    with pytest.raises(ProviderError):
        controls.controlled_call(Provider.grok, "one")
    with pytest.raises(ProviderError):
        controls.controlled_call(Provider.grok, "two")
    with pytest.raises(controls.CircuitOpenError):
        controls.controlled_call(Provider.grok, "three")


def test_rate_limiter_is_bounded():
    limiter = controls.SlidingWindowRateLimiter()
    assert limiter.allow("client", limit=2, window_seconds=60)
    assert limiter.allow("client", limit=2, window_seconds=60)
    assert not limiter.allow("client", limit=2, window_seconds=60)


def test_cancellation_registry_blocks_cancelled_conversation():
    controls.cancellation_registry.cancel("conv-123")
    with pytest.raises(controls.RequestCancelledError):
        controls.cancellation_registry.require_active("conv-123")
