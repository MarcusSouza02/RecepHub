import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def client():
    app = create_app(Settings(_env_file=None))
    with TestClient(app) as client:
        yield client
