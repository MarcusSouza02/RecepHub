from unittest.mock import Mock

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.database.session import get_session


def test_health_does_not_require_database(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_queries_database(client):
    session = Mock()
    client.app.dependency_overrides[get_session] = lambda: session
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    assert str(session.execute.call_args.args[0]) == "SELECT 1"


def test_ready_hides_database_error(client):
    session = Mock()
    session.execute.side_effect = OperationalError("secret connection", {}, Exception("secret"))
    client.app.dependency_overrides[get_session] = lambda: session
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json() == {"detail": "Banco de dados indisponível"}
    assert "secret" not in response.text


def test_cors_allows_only_configured_origin(client):
    allowed = client.get("/health", headers={"Origin": "http://localhost:3000"})
    denied = client.get("/health", headers={"Origin": "https://untrusted.example"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-origin" not in denied.headers


def test_cors_preflight_rejects_write_method(client):
    response = client.options(
        "/health",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 400


@pytest.mark.parametrize("origin", ["*", "https://example.com/path", "file://example"])
def test_settings_reject_unsafe_origins(origin):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, cors_origins=[origin])


def test_docs_and_openapi_available(client):
    assert client.get("/docs").status_code == 200
    assert "/api/v1/health/ready" in client.get("/openapi.json").json()["paths"]


def test_unexpected_error_is_sanitized(client):
    from fastapi.testclient import TestClient

    @client.app.get("/test-error")
    def fail():
        raise RuntimeError("sensitive data")

    with TestClient(client.app, raise_server_exceptions=False) as safe_client:
        response = safe_client.get("/test-error")
    assert response.status_code == 500
    assert response.json() == {"detail": "Erro interno do servidor"}
