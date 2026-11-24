import pytest
from fastapi.testclient import TestClient

from app.api.v1.auth import require_auth
from app.api.v1.dashboard import operational_summary, router
from app.database.session import get_session
from app.models.employee import Employee
from app.models.unit import Unit


def dashboard_app():
    from app.core.config import Settings
    from app.main import create_app

    app = create_app(Settings(_env_file=None))
    app.include_router(router, prefix="/api/v1")
    return app


def test_dashboard_requires_session():
    with TestClient(dashboard_app()) as client:
        response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.integration
def test_summary_counts_real_active_records_and_preserved_inactive_links(db_session):
    assert operational_summary(db_session) == {
        "active_units": 0,
        "active_employees": 0,
        "active_employees_without_home_unit": 0,
    }
    active = Unit(name="Unidade Fictícia Ativa", active=True)
    inactive = Unit(name="Unidade Fictícia Inativa", active=False)
    db_session.add_all([active, inactive])
    db_session.flush()
    db_session.add_all(
        [
            Employee(display_name="Fictícia vinculada", active=True, home_unit_id=active.id),
            Employee(display_name="Fictícia preservada", active=True, home_unit_id=inactive.id),
            Employee(display_name="Fictícia sem unidade", active=True),
            Employee(display_name="Fictícia inativa", active=False),
        ]
    )
    db_session.flush()
    assert operational_summary(db_session) == {
        "active_units": 1,
        "active_employees": 3,
        "active_employees_without_home_unit": 1,
    }
    active.active = False
    db_session.flush()
    assert operational_summary(db_session)["active_units"] == 0
    assert operational_summary(db_session)["active_employees_without_home_unit"] == 1


@pytest.mark.integration
def test_dashboard_endpoint_returns_uncached_summary(db_session):
    app = dashboard_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[require_auth] = lambda: {"username": "fictional"}
    with TestClient(app) as client:
        response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "active_units": 0,
        "active_employees": 0,
        "active_employees_without_home_unit": 0,
    }
