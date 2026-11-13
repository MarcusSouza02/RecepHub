import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.auth import require_auth
from app.core.config import Settings
from app.database.session import get_session
from app.main import create_app
from app.schemas.employees import EmployeeCreate
from app.services.employees import EmployeeService
from app.services.work_patterns import WorkPatternService


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/employees/{value}"),
        ("PATCH", "/api/v1/employees/{value}"),
        ("GET", "/api/v1/units/{value}/employees"),
        ("GET", "/api/v1/employees/{value}/work-patterns"),
        ("PUT", "/api/v1/employees/{value}/work-patterns"),
        ("GET", "/api/v1/units/{value}"),
    ],
)
def test_authenticated_malformed_uuid_is_sanitized_and_never_cached(method, path):
    app = create_app(Settings(_env_file=None))
    app.dependency_overrides[require_auth] = lambda: {"username": "fictional"}
    app.dependency_overrides[get_session] = lambda: None
    marker = "fictional-private-input-do-not-echo"
    with TestClient(app) as client:
        response = client.request(
            method,
            path.format(value=marker),
            headers={"Origin": "http://localhost:3000", "X-RecepHub-CSRF": "1"},
            json={},
        )
    assert response.status_code == 422
    assert "no-store" in response.headers["cache-control"]
    assert marker not in response.text
    assert isinstance(response.json()["detail"], str)
    assert "input" not in response.json()
    assert "ctx" not in response.json()


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/units"),
        ("POST", "/api/v1/units"),
        ("GET", "/api/v1/employees"),
        ("POST", "/api/v1/employees"),
        ("GET", "/api/v1/units/00000000-0000-0000-0000-000000000000/employees"),
        ("GET", "/api/v1/employees/00000000-0000-0000-0000-000000000000/work-patterns"),
        ("PUT", "/api/v1/employees/00000000-0000-0000-0000-000000000000/work-patterns"),
        ("GET", "/api/v1/dashboard/summary"),
    ],
)
def test_operational_routes_require_backend_authentication(method, path):
    app = create_app(Settings(_env_file=None))
    app.dependency_overrides[get_session] = lambda: None
    with TestClient(app) as client:
        response = client.request(method, path, json={})
    assert response.status_code == 401
    assert "no-store" in response.headers["cache-control"]


@pytest.mark.integration
def test_failed_weekly_commit_returns_503_and_rolls_back_all_days(db_session, monkeypatch):
    employee = EmployeeService(db_session).create(
        EmployeeCreate(display_name="Pessoa fictícia atomicidade")
    )
    employee_id = employee["id"]
    initial = WorkPatternService(db_session).get(employee_id)
    app = create_app(Settings(_env_file=None))
    app.dependency_overrides[require_auth] = lambda: {"username": "fictional"}

    def request_session():
        # Same connection, separate savepoint: disposal reproduces the production
        # request lifecycle without allowing a test to commit its outer transaction.
        with Session(bind=db_session.bind, join_transaction_mode="create_savepoint") as session:

            def failed_commit():
                session.flush()
                raise SQLAlchemyError("fictional-private-database-error")

            monkeypatch.setattr(session, "commit", failed_commit)
            yield session

    app.dependency_overrides[get_session] = request_session
    with TestClient(app) as client:
        response = client.put(
            f"/api/v1/employees/{employee_id}/work-patterns",
            headers={"Origin": "http://localhost:3000", "X-RecepHub-CSRF": "1"},
            json={"days": [{"weekday": day, "state": "non_working"} for day in range(7)]},
        )
    assert response.status_code == 503
    assert "fictional-private" not in response.text
    assert "no-store" in response.headers["cache-control"]
    db_session.expire_all()
    assert WorkPatternService(db_session).get(employee_id) == initial
