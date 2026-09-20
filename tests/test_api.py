import uuid

from fastapi.testclient import TestClient

import app.main as main_module
from app.schemas import GatewayResponse


def test_web_console_is_served():
    with TestClient(main_module.app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "Open Agent Collaboration Gateway" in response.text
        assert "Start collaboration" in response.text


def test_health_endpoint():
    with TestClient(main_module.app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["version"] == "0.2.0"


def test_providers_endpoint_does_not_expose_keys():
    with TestClient(main_module.app) as client:
        response = client.get("/providers")
        assert response.status_code == 200
        body = response.json()
        assert {p["name"] for p in body["providers"]} == {"openai", "grok"}
        assert "api_key" not in str(body).lower()


def test_access_token_is_enforced_when_configured(monkeypatch):
    monkeypatch.setattr(main_module.settings, "oacg_access_token", "test-secret")

    with TestClient(main_module.app) as client:
        denied = client.post(
            "/ask",
            json={"provider": "openai", "prompt": "hello", "risk_level": "low"},
        )
        assert denied.status_code == 401

        # Authentication succeeds; request then reaches the provider layer and fails because
        # the test environment does not provide a live API key.
        allowed = client.post(
            "/ask",
            headers={"X-OACG-Token": "test-secret"},
            json={"provider": "openai", "prompt": "hello", "risk_level": "low"},
        )
        assert allowed.status_code != 401


def test_idempotency_returns_cached_response(monkeypatch):
    monkeypatch.setattr(main_module.settings, "oacg_access_token", "")
    calls = {"count": 0}

    def fake_ask(*args, **kwargs):
        calls["count"] += 1
        return GatewayResponse(
            conversation_id="conv-test",
            trace_id="trace-test",
            status="completed",
            messages=[],
            final="cached-result",
        )

    monkeypatch.setattr(main_module, "ask", fake_ask)

    key = f"test-{uuid.uuid4()}"
    payload = {
        "provider": "openai",
        "prompt": "idempotent request",
        "risk_level": "low",
        "idempotency_key": key,
    }

    with TestClient(main_module.app) as client:
        first = client.post("/ask", json=payload)
        second = client.post("/ask", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert calls["count"] == 1


def test_idempotency_key_conflict_is_rejected(monkeypatch):
    monkeypatch.setattr(main_module.settings, "oacg_access_token", "")

    def fake_ask(*args, **kwargs):
        return GatewayResponse(
            conversation_id="conv-test",
            trace_id="trace-test",
            status="completed",
            messages=[],
            final="ok",
        )

    monkeypatch.setattr(main_module, "ask", fake_ask)

    key = f"test-{uuid.uuid4()}"
    with TestClient(main_module.app) as client:
        first = client.post(
            "/ask",
            json={
                "provider": "openai",
                "prompt": "first",
                "risk_level": "low",
                "idempotency_key": key,
            },
        )
        conflict = client.post(
            "/ask",
            json={
                "provider": "openai",
                "prompt": "different",
                "risk_level": "low",
                "idempotency_key": key,
            },
        )

    assert first.status_code == 200
    assert conflict.status_code == 409


def test_cancel_endpoint_marks_conversation_cancelled(monkeypatch):
    monkeypatch.setattr(main_module.settings, "oacg_access_token", "")
    main_module.cancellation_registry.reset()

    with TestClient(main_module.app) as client:
        response = client.post("/conversations/conv-cancel/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancel_requested"
    assert main_module.cancellation_registry.is_cancelled("conv-cancel")
