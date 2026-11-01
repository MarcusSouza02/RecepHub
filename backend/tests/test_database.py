import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import Settings
from app.database.session import get_session
from app.main import create_app


@pytest.mark.integration
def test_postgres_connection_and_ready():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Defina TEST_DATABASE_URL apontando para PostgreSQL descartável")
    engine = create_engine(url, connect_args={"connect_timeout": 3})
    from sqlalchemy.orm import Session

    def session_override():
        with Session(engine) as session:
            yield session

    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
        app = create_app(Settings(_env_file=None))
        app.dependency_overrides[get_session] = session_override
        with TestClient(app) as client:
            assert client.get("/api/v1/health/ready").json() == {"status": "ok", "database": "ok"}
    finally:
        engine.dispose()
