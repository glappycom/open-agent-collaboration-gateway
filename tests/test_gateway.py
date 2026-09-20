import os
from pathlib import Path

os.environ["DATABASE_PATH"] = "/tmp/oacg_test.db"
os.environ["MAX_TURNS"] = "4"
os.environ["MAX_PROMPT_CHARS"] = "120"

from app import gateway
from app.db import init_db
from app.providers import CallResult
from app.schemas import CollaborateRequest, Provider, RiskLevel


def setup_module():
    p = Path("/tmp/oacg_test.db")
    if p.exists():
        p.unlink()
    init_db()


def test_high_risk_requires_approval():
    req = CollaborateRequest(task="Deploy production change", risk_level=RiskLevel.high, approved=False)
    result = gateway.collaborate(req)
    assert result.status == "approval_required"
    assert result.trace_id


def test_bounded_turns_synthesis_and_broker_identifiers(monkeypatch):
    monkeypatch.setattr(gateway.settings, "max_turns", 4)
    calls = []

    def fake_call(provider, prompt, system_context=None):
        calls.append(provider.value)
        return CallResult(
            text=f"response-{len(calls)}-{provider.value}",
            model=f"test-{provider.value}",
            latency_ms=7,
        )

    monkeypatch.setattr(gateway, "call_model", fake_call)
    req = CollaborateRequest(task="Design a small API", starter=Provider.openai, turns=10, approved=True)
    result = gateway.collaborate(req)

    assert result.status == "completed"
    assert len(result.messages) == 4
    assert calls[:4] == ["openai", "grok", "openai", "grok"]
    assert calls[-1] == "openai"
    assert result.final.startswith("response-")
    assert result.final_message_id
    assert result.final_schema_version == "1.0"

    message_ids = {m.message_id for m in result.messages}
    assert len(message_ids) == 4
    assert all(m.trace_id == result.trace_id for m in result.messages)
    assert [m.sequence for m in result.messages] == [2, 4, 6, 8]
    assert all(m.recipient == "host" for m in result.messages)
    assert result.messages[0].sender == "openai"
    assert result.messages[1].sender == "grok"
    assert result.messages[0].model == "test-openai"
    assert result.messages[0].latency_ms == 7


def test_prompt_limit(monkeypatch):
    monkeypatch.setattr(gateway.settings, "max_prompt_chars", 120)
    try:
        gateway._validate_text("prompt", "x" * 121)
    except ValueError as exc:
        assert "MAX_PROMPT_CHARS" in str(exc)
    else:
        raise AssertionError("expected prompt limit failure")
