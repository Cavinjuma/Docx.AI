import logging

import pytest
from fastapi.testclient import TestClient

from app import __version__


def test_root_returns_service_status_and_api_links(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app": "AI Document Intelligence Platform",
        "docs": "/api/docs",
        "health": "/api/health",
    }


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app": "AI Document Intelligence Platform",
        "version": __version__,
        "environment": "test",
    }


def test_openapi_docs_are_served(client: TestClient) -> None:
    assert client.get("/api/openapi.json").status_code == 200
    assert client.get("/api/docs").status_code == 200


def test_request_is_logged_with_timing_and_without_query_string(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="app.request"):
        client.get("/api/health?token=secret")
    # Scope to our own logger: httpx (the test client) logs full URLs itself.
    records = [r for r in caplog.records if r.name == "app.request"]
    assert len(records) == 1
    record = records[0]
    assert record.path == "/api/health"
    assert record.status_code == 200
    assert record.duration_ms >= 0
    assert "secret" not in record.getMessage()
    assert "secret" not in str(record.__dict__)


def test_cors_allows_configured_origin_only(client: TestClient) -> None:
    def preflight(origin: str) -> str | None:
        r = client.options(
            "/api/health",
            headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
        )
        return r.headers.get("access-control-allow-origin")

    assert preflight("http://allowed.test") == "http://allowed.test"
    assert preflight("http://evil.test") is None
