from app import db, telemetry
from app.providers import CallResult
from app.schemas import Provider


def test_estimated_cost_uses_configured_rates(monkeypatch):
    monkeypatch.setattr(telemetry.settings, "openai_input_cost_per_million", 2.0)
    monkeypatch.setattr(telemetry.settings, "openai_output_cost_per_million", 4.0)

    result = CallResult(
        text="ok",
        model="test",
        latency_ms=10,
        input_tokens=1_000_000,
        output_tokens=500_000,
        total_tokens=1_500_000,
    )

    assert telemetry.estimate_cost_usd(Provider.openai, result) == 4.0


def test_cost_is_unavailable_when_rates_are_not_configured(monkeypatch):
    monkeypatch.setattr(telemetry.settings, "xai_input_cost_per_million", 0.0)
    monkeypatch.setattr(telemetry.settings, "xai_output_cost_per_million", 0.0)

    result = CallResult(
        text="ok",
        model="test",
        latency_ms=10,
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
    )

    assert telemetry.estimate_cost_usd(Provider.grok, result) is None


def test_provider_telemetry_persists_without_prompt_content(monkeypatch, tmp_path):
    database = tmp_path / "telemetry.db"
    monkeypatch.setattr(db.settings, "database_path", str(database))
    db.init_db()

    result = CallResult(
        text="sensitive model output that should not be in metrics",
        model="test-model",
        latency_ms=42,
        input_tokens=10,
        output_tokens=5,
        total_tokens=15,
        attempts=2,
    )

    metadata = telemetry.record_provider_result(
        trace_id="trace-1",
        conversation_id="conv-1",
        provider=Provider.openai,
        result=result,
        turn=1,
    )

    events = db.load_trace_telemetry("trace-1")
    assert len(events) == 1
    assert events[0]["event_type"] == "provider_response"
    assert events[0]["latency_ms"] == 42
    assert events[0]["retry_count"] == 1
    assert events[0]["input_tokens"] == 10
    assert "sensitive model output" not in str(events[0])
    assert metadata["retry_count"] == 1

    summary = db.telemetry_summary()
    assert summary["provider_calls"] == 1
    assert summary["total_tokens"] == 15
