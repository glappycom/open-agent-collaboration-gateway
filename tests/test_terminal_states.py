import pytest

from app import controls, db, gateway
from app.providers import CallResult, ProviderError, ProviderTimeoutError
from app.schemas import CollaborateRequest, Provider, TerminalState


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch, tmp_path):
    database = tmp_path / "terminal.db"
    monkeypatch.setattr(db.settings, "database_path", str(database))
    db.init_db()
    controls.reset_circuit_breakers()
    controls.cancellation_registry.reset()
    monkeypatch.setattr(gateway.settings, "max_turns", 4)
    monkeypatch.setattr(gateway.settings, "max_provider_calls_per_request", 5)
    monkeypatch.setattr(gateway.settings, "max_fallback_calls_per_request", 1)


def test_provider_unavailable_is_explicit_terminal_state(monkeypatch):
    def unavailable(provider, prompt, system_context=None):
        raise ProviderError("provider unavailable")

    monkeypatch.setattr(gateway, "controlled_call", unavailable)

    result = gateway.collaborate(
        CollaborateRequest(task="test", turns=1, approved=True)
    )

    assert result.status == "failed"
    assert result.terminal_state == TerminalState.provider_unavailable
    assert not result.messages


def test_timeout_is_explicit_terminal_state(monkeypatch):
    def timeout(provider, prompt, system_context=None):
        raise ProviderTimeoutError("provider request timed out")

    monkeypatch.setattr(gateway, "controlled_call", timeout)

    result = gateway.collaborate(
        CollaborateRequest(task="test", turns=1, approved=True)
    )

    assert result.status == "failed"
    assert result.terminal_state == TerminalState.timed_out


def test_cancelled_conversation_is_explicit_terminal_state():
    controls.cancellation_registry.cancel("conv-cancelled")

    result = gateway.collaborate(
        CollaborateRequest(
            task="test",
            conversation_id="conv-cancelled",
            turns=1,
            approved=True,
        )
    )

    assert result.status == "failed"
    assert result.terminal_state == TerminalState.cancelled


def test_final_synthesis_failure_returns_bounded_partial(monkeypatch):
    calls = {"count": 0}

    def one_success_then_fail(provider, prompt, system_context=None):
        calls["count"] += 1
        if calls["count"] == 1:
            return CallResult(
                text="useful partial contribution",
                model="test-provider",
                latency_ms=1,
            )
        raise ProviderError("final provider unavailable")

    monkeypatch.setattr(gateway, "controlled_call", one_success_then_fail)

    result = gateway.collaborate(
        CollaborateRequest(task="test", turns=1, approved=True)
    )

    assert result.status == "partial"
    assert result.terminal_state == TerminalState.partial
    assert result.final == "useful partial contribution"
    assert len(result.messages) == 1
    assert "final synthesis unavailable" in result.terminal_reason


def test_single_bounded_fallback_can_complete_collaboration(monkeypatch):
    calls = []

    def primary_then_fallback(provider, prompt, system_context=None):
        calls.append(provider)
        if len(calls) == 1 and provider == Provider.openai:
            raise ProviderError("primary unavailable")
        return CallResult(
            text=f"answer from {provider.value}",
            model=f"test-{provider.value}",
            latency_ms=1,
        )

    monkeypatch.setattr(gateway, "controlled_call", primary_then_fallback)

    result = gateway.collaborate(
        CollaborateRequest(
            task="test",
            starter=Provider.openai,
            fallback_provider=Provider.grok,
            turns=1,
            approved=True,
        )
    )

    assert result.status == "completed"
    assert result.terminal_state == TerminalState.completed
    assert result.fallback_provider == Provider.grok
    assert result.messages[0].provider == Provider.grok
    assert calls == [Provider.openai, Provider.grok, Provider.openai]


def test_fallback_budget_does_not_recurse(monkeypatch):
    calls = []

    def always_unavailable(provider, prompt, system_context=None):
        calls.append(provider)
        raise ProviderError(f"{provider.value} unavailable")

    monkeypatch.setattr(gateway, "controlled_call", always_unavailable)

    result = gateway.collaborate(
        CollaborateRequest(
            task="test",
            starter=Provider.openai,
            fallback_provider=Provider.grok,
            turns=1,
            approved=True,
        )
    )

    assert result.terminal_state == TerminalState.provider_unavailable
    assert calls == [Provider.openai, Provider.grok]
