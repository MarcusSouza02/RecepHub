from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1.auth import require_auth
from app.core.config import Settings
from app.database.session import get_session
from app.main import create_app
from app.models.unit import Unit
from app.schemas.employees import EmployeeCreate, EmployeePatch, EmployeeQuery
from app.services.auth import AuthError
from app.services.employees import EmployeeService


def test_employee_inputs_trim_and_reject_invalid_values():
    assert EmployeeCreate(display_name="  Pessoa Fictícia  ").display_name == "Pessoa Fictícia"
    for name in ("", "   ", "x" * 141):
        with pytest.raises(ValidationError):
            EmployeeCreate(display_name=name)
    for values in ({}, {"active": None}, {"display_name": None}, {"active": "true"}):
        with pytest.raises(ValidationError):
            EmployeePatch(**values)
    assert EmployeePatch(home_unit_id=None).model_dump(exclude_unset=True) == {"home_unit_id": None}


def test_employee_filter_validation():
    for values in (
        {"page": 0},
        {"page_size": 101},
        {"status": "unknown"},
        {"home_unit_id": uuid4(), "without_home_unit": True},
    ):
        with pytest.raises(ValidationError):
            EmployeeQuery(**values)


@pytest.mark.integration
def test_employee_links_preserve_inactive_unit_and_allow_removal(db_session):
    unit = Unit(name="Unidade Fictícia Azul", active=True)
    db_session.add(unit)
    db_session.commit()
    service = EmployeeService(db_session)
    created = service.create(EmployeeCreate(display_name="Pessoa Fictícia", home_unit_id=unit.id))
    unit.active = False
    db_session.commit()
    changed = service.patch(
        created["id"], EmployeePatch(notes="Observação fictícia", home_unit_id=unit.id)
    )
    assert changed["home_unit_id"] == unit.id
    assert changed["home_unit_active"] is False
    with pytest.raises(AuthError) as error:
        service.create(EmployeeCreate(display_name="Outra Pessoa Fictícia", home_unit_id=unit.id))
    assert error.value.status == 409
    db_session.rollback()
    cleared = service.patch(created["id"], EmployeePatch(home_unit_id=None))
    assert cleared["home_unit_id"] is None
    assert cleared["home_unit_active"] is None


@pytest.mark.integration
def test_employee_names_may_repeat_and_pagination_is_stable(db_session):
    service = EmployeeService(db_session)
    for _ in range(3):
        service.create(EmployeeCreate(display_name="Homônima Fictícia"))
    service.create(EmployeeCreate(display_name="Inativa Fictícia", active=False))
    first = service.list(EmployeeQuery(q="Homônima", page_size=2))
    second = service.list(EmployeeQuery(q="Homônima", page=2, page_size=2))
    assert first["total"] == second["total"] == 3
    ids = [row["id"] for row in first["items"] + second["items"]]
    assert len(set(ids)) == 3
    assert ids == sorted(ids)
    assert service.list(EmployeeQuery(status="inactive"))["total"] == 1
    assert service.list(EmployeeQuery(without_home_unit=True, status="all"))["total"] == 4


@pytest.mark.integration
def test_employee_missing_links_are_rejected(db_session):
    service = EmployeeService(db_session)
    with pytest.raises(AuthError) as error:
        service.create(EmployeeCreate(display_name="Pessoa Fictícia", home_unit_id=uuid4()))
    assert error.value.status == 404
    with pytest.raises(AuthError) as error:
        service.get(uuid4())
    assert error.value.status == 404


@pytest.fixture
def employees_client(db_session):
    app = create_app(Settings(_env_file=None))
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[require_auth] = lambda: {"username": "fictional"}
    with TestClient(app) as client:
        yield client


@pytest.mark.integration
def test_employee_api_validation_and_lifecycle(employees_client):
    client = employees_client
    url = "/api/v1/employees"
    headers = {"Origin": "http://localhost:3000", "X-RecepHub-CSRF": "1"}
    assert client.post(url, json={"display_name": "Fictícia"}).status_code == 403
    created = client.post(url, headers=headers, json={"display_name": " Pessoa Fictícia "})
    assert created.status_code == 201
    employee = created.json()
    assert employee["display_name"] == "Pessoa Fictícia"
    assert employee["home_unit_name"] is None
    path = f"{url}/{employee['id']}"
    assert client.get(path).status_code == 200
    assert client.patch(path, headers=headers, json={"active": False}).status_code == 200
    assert client.get(url).json()["total"] == 0
    assert client.get(url, params={"status": "inactive"}).json()["total"] == 1
    assert client.get(url, params={"page_size": 101}).status_code == 422
    assert (
        client.get(
            url, params={"home_unit_id": str(uuid4()), "without_home_unit": "true"}
        ).status_code
        == 422
    )
    assert client.get(f"/api/v1/units/{uuid4()}/employees").status_code == 404
    assert client.patch(path, headers=headers, json={}).status_code == 422
    assert client.delete(path).status_code == 405
