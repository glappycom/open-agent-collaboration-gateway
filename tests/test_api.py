from fastapi.testclient import TestClient

from app.main import app


def test_web_console_is_served():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "Open Agent Collaboration Gateway" in response.text
        assert "Start collaboration" in response.text


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["version"] == "0.2.0"


def test_providers_endpoint_does_not_expose_keys():
    with TestClient(app) as client:
        response = client.get("/providers")
        assert response.status_code == 200
        body = response.json()
        assert {p["name"] for p in body["providers"]} == {"openai", "grok"}
        assert "api_key" not in str(body).lower()
