import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database.session import get_session
from app.main import create_app
from tests.database import require_test_database_reset, validate_test_database_url


@pytest.mark.parametrize(
    "url",
    [
        "not-a-url",
        "sqlite:///recephub_test",
        "postgresql://user:example@localhost/recephub_test",
        "postgresql+psycopg://user:example@localhost/recephub",
        "postgresql+psycopg://user:example@localhost/recephub_test_backup",
        "postgresql+psycopg://user:example@localhost/",
        "postgresql+psycopg://user:example@localhost/recephub_test?options=other",
    ],
)
def test_reject_unsafe_test_database_url(url):
    with pytest.raises(ValueError):
        validate_test_database_url(url)


def test_accept_explicit_test_database_url():
    url = validate_test_database_url("postgresql+psycopg://test:example@localhost/recephub_test")
    assert url.database == "recephub_test"


@pytest.mark.parametrize("value", [None, "", "0", "true"])
def test_migrations_require_explicit_reset_opt_in(value):
    with pytest.raises(ValueError, match="TEST_DATABASE_ALLOW_RESET=1"):
        require_test_database_reset(value)


def test_accept_explicit_reset_opt_in():
    require_test_database_reset("1")


@pytest.mark.integration
def test_postgres_connection_and_ready(postgres_engine):
    def session_override():
        with Session(postgres_engine) as session:
            yield session

    with postgres_engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
    app = create_app(Settings(_env_file=None))
    app.dependency_overrides[get_session] = session_override
    with TestClient(app) as client:
        assert client.get("/api/v1/health/ready").json() == {"status": "ok", "database": "ok"}
