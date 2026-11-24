from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.api.v1.auth import require_auth
from app.core.config import Settings
from app.database.session import get_session
from app.main import create_app
from app.models.unit import Unit
from app.schemas.units import UnitCreate, UnitPatch

HEADERS = {"Origin": "http://localhost:3000", "X-RecepHub-CSRF": "1"}
URL = "/api/v1/units"


@pytest.mark.parametrize(
    "data",
    [
        {"name": " "},
        {"name": "x" * 121},
        {"name": "A", "active": 1},
        {"name": "A", "secret": "hidden"},
    ],
)
def test_invalid_unit_create(data):
    with pytest.raises(ValidationError):
        UnitCreate.model_validate(data)


@pytest.mark.parametrize("data", [{}, {"name": None}, {"active": None}])
def test_invalid_unit_patch(data):
    with pytest.raises(ValidationError):
        UnitPatch.model_validate(data)


def test_unit_trimming_and_clear_optional_fields():
    data = UnitCreate(name="  Unidade Fictícia  ", city=" ", description=" exemplo ")
    assert data.name == "Unidade Fictícia"
    assert data.city is None
    assert data.description == "exemplo"
    assert UnitPatch(city=None).model_dump(exclude_unset=True) == {"city": None}


@pytest.fixture
def units_client(db_session):
    app = create_app(Settings(_env_file=None))
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[require_auth] = lambda: {"username": "fictional"}
    with TestClient(app) as client:
        yield client


def test_units_lifecycle_and_duplicate_names(units_client):
    client = units_client
    created = client.post(
        URL, headers=HEADERS, json={"name": " Unidade Fictícia ", "city": "Cidade Exemplo"}
    )
    assert created.status_code == 201
    unit = created.json()
    assert unit["name"] == "Unidade Fictícia"
    assert unit["active"] is True
    assert unit["created_at"] and unit["updated_at"]
    assert client.post(URL, headers=HEADERS, json={"name": unit["name"]}).status_code == 201
    path = f"{URL}/{unit['id']}"
    assert client.get(path).status_code == 200
    updated = client.patch(path, headers=HEADERS, json={"active": False, "city": None})
    assert updated.status_code == 200
    assert updated.json()["city"] is None
    assert client.get(URL).json()["total"] == 1
    assert client.get(URL, params={"status": "inactive"}).json()["total"] == 1
    assert client.get(URL, params={"status": "all", "page_size": 1}).json()["total"] == 2
    assert client.patch(path, headers=HEADERS, json={"active": True}).json()["active"] is True
    assert client.delete(path).status_code == 405


def test_units_literal_search_and_pagination(units_client):
    for name in ["Alfa", "Unidade 10%", "Unidade_Exemplo", "Unidade Fictícia"]:
        assert units_client.post(URL, headers=HEADERS, json={"name": name}).status_code == 201
    for literal in ["%", "_"]:
        result = units_client.get(URL, params={"q": literal}).json()
        assert result["total"] == 1
    result = units_client.get(URL, params={"page_size": 2, "page": 2}).json()
    assert result["total"] == 4
    assert len(result["items"]) == 2
    assert units_client.get(URL, params={"q": "alFA"}).json()["items"][0]["name"] == "Alfa"


def test_units_sanitized_validation_and_guards(units_client):
    secret = "fictional-sensitive-input"
    response = units_client.post(URL, headers=HEADERS, json={"name": "A", "unexpected": secret})
    assert response.status_code == 422
    assert secret not in response.text
    assert units_client.post(URL, json={"name": "A"}).status_code == 403
    assert units_client.post(URL, headers=HEADERS, content="x").status_code == 415
    assert (
        units_client.post(
            URL, headers={**HEADERS, "Content-Type": "application/json"}, content="x" * 4097
        ).status_code
        == 413
    )
    for query in [{"page": 0}, {"page_size": 101}, {"status": "unknown"}]:
        assert units_client.get(URL, params=query).status_code == 422
    assert units_client.get(f"{URL}/invalid").status_code == 422
    assert units_client.get(f"{URL}/{uuid4()}").status_code == 404
    assert (
        units_client.patch(f"{URL}/{uuid4()}", headers=HEADERS, json={"active": False}).status_code
        == 404
    )


def test_units_database_rejects_blank_name(db_session):
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(Unit(name=" "))
        db_session.flush()
