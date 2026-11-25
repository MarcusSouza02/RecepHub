from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select

from app.api.v1.auth import require_auth
from app.core.config import Settings
from app.database.session import get_session
from app.main import create_app
from app.models.employee_work_pattern import EmployeeWorkPattern
from app.models.unit import Unit
from app.schemas.employees import EmployeeCreate
from app.schemas.schedules import (
    AssignmentCreate,
    AssignmentPatch,
    AssignmentTimes,
    DayPatch,
    PublishInput,
    ScheduleCreate,
    ScheduleQuery,
    VersionInput,
)
from app.schemas.work_patterns import WorkPatternPut
from app.services.auth import AuthError
from app.services.employees import EmployeeService
from app.services.schedules import ScheduleService
from app.services.work_patterns import WorkPatternService


def test_schedule_inputs_reject_ambiguous_or_invalid_data():
    assert ScheduleCreate(week_start="2026-11-23").week_start == date(2026, 11, 23)
    for values in ({"week_start": "2026-11-24"}, {"week_start": "2026-11-23", "extra": 1}):
        with pytest.raises(ValidationError):
            ScheduleCreate(**values)
    for values in (
        {"start_time": "17:00", "end_time": "08:00"},
        {"start_time": "08:00:01", "end_time": "17:00"},
        {"start_time": "08:00", "end_time": "17:00", "break_start_time": "12:00"},
        {
            "start_time": "08:00",
            "end_time": "17:00",
            "break_start_time": "07:00",
            "break_end_time": "09:00",
        },
    ):
        with pytest.raises(ValidationError):
            AssignmentTimes(**values)
    with pytest.raises(ValidationError):
        DayPatch(expected_version=1, state="excluded", resolution_note="  ")
    with pytest.raises(ValidationError):
        VersionInput(expected_version=True)
    with pytest.raises(ValidationError):
        PublishInput(expected_version=1, confirmed=False)
    with pytest.raises(ValidationError):
        AssignmentPatch(expected_version=1)
    with pytest.raises(ValidationError):
        ScheduleQuery(from_date="2026-12-01", to_date="2026-11-01")
    with pytest.raises(ValidationError):
        PublishInput(expected_version=1, confirmed=1)
    with pytest.raises(ValidationError):
        AssignmentTimes(start_time=3600, end_time="17:00")
    with pytest.raises(ValidationError):
        AssignmentPatch(expected_version=1, start_time=3600)
    with pytest.raises(ValidationError):
        ScheduleCreate(week_start="9999-12-27")


def test_schedule_endpoints_require_session(client):
    for method, path in (
        ("get", "/api/v1/schedules"),
        ("post", "/api/v1/schedules"),
        ("get", f"/api/v1/schedules/{uuid4()}"),
        ("post", f"/api/v1/schedules/{uuid4()}/publish"),
        ("get", f"/api/v1/schedules/{uuid4()}/revisions"),
    ):
        response = getattr(client, method)(path)
        assert response.status_code == 401
        assert response.headers["cache-control"] == "no-store"


def prepare(db):
    unit = Unit(name="Unidade Fictícia Escalas")
    db.add(unit)
    db.commit()
    employee = EmployeeService(db).create(
        EmployeeCreate(display_name="Pessoa Fictícia Escalas", home_unit_id=unit.id)
    )
    days = [{"weekday": i, "state": "non_working"} for i in range(7)]
    days[0] = {"weekday": 0, "state": "working", "start_time": "08:00", "end_time": "12:00"}
    WorkPatternService(db).put(employee["id"], WorkPatternPut(days=days))
    return unit, employee


@pytest.mark.integration
def test_schedule_generation_is_frozen_and_duplicate_rejected(db_session):
    unit, employee = prepare(db_session)
    service = ScheduleService(db_session)
    created = service.create(ScheduleCreate(week_start="2026-11-23"))
    assert len(created["days"]) == 7
    monday = created["days"][0]
    assert monday["state"] == "working"
    assert monday["assignments"][0]["unit_name"] == unit.name
    assert not created["diagnostics"]["errors"]
    pattern = db_session.scalar(
        select(EmployeeWorkPattern).where(
            EmployeeWorkPattern.employee_id == employee["id"], EmployeeWorkPattern.weekday == 0
        )
    )
    pattern.state, pattern.start_time, pattern.end_time = "non_working", None, None
    unit.name = "Nome Fictício Alterado"
    db_session.commit()
    unchanged = service.detail(created["id"])
    assert unchanged["days"][0]["assignments"][0]["unit_name"] == "Unidade Fictícia Escalas"
    unchanged = service.patch_assignment(
        created["id"],
        monday["assignments"][0]["id"],
        AssignmentPatch(expected_version=1, unit_id=unit.id, position="Atividade fictícia"),
    )
    assert unchanged["days"][0]["assignments"][0]["unit_name"] == "Unidade Fictícia Escalas"
    assert service.list(ScheduleQuery(from_date="0001-01-01"))["total"] == 1
    with pytest.raises(AuthError) as error:
        service.create(ScheduleCreate(week_start="2026-11-23"))
    assert error.value.status == 409


@pytest.mark.integration
def test_schedule_multiple_shifts_overlap_atomicity_and_version(db_session):
    unit, _ = prepare(db_session)
    service = ScheduleService(db_session)
    created = service.create(ScheduleCreate(week_start="2026-11-23"))
    day = created["days"][0]
    with pytest.raises(AuthError) as error:
        service.add_assignment(
            created["id"],
            AssignmentCreate(
                expected_version=1,
                day_id=day["id"],
                unit_id=unit.id,
                start_time="11:00",
                end_time="14:00",
            ),
        )
    assert error.value.status == 409
    detail = service.detail(created["id"])
    assert detail["version"] == 1 and len(detail["days"][0]["assignments"]) == 1
    updated = service.add_assignment(
        created["id"],
        AssignmentCreate(
            expected_version=1,
            day_id=day["id"],
            unit_id=unit.id,
            start_time="12:00",
            end_time="14:00",
        ),
    )
    assert updated["version"] == 2
    with pytest.raises(AuthError) as error:
        service.patch_day(created["id"], day["id"], DayPatch(expected_version=1, state="pending"))
    assert error.value.status == 409
    assert (
        db_session.scalar(
            select(EmployeeWorkPattern).where(EmployeeWorkPattern.weekday == 0)
        ).end_time.hour
        == 12
    )


@pytest.mark.integration
def test_schedule_publication_revisions_preserve_snapshot(db_session):
    unit, _ = prepare(db_session)
    service = ScheduleService(db_session)
    created = service.create(ScheduleCreate(week_start="2026-11-23"))
    first = service.publish(created["id"], PublishInput(expected_version=1, confirmed=True))
    assert first["number"] == 1
    assert first["snapshot"]["days"][0]["assignments"][0]["unit_name"] == unit.name
    detail = service.detail(created["id"])
    assignment = detail["days"][0]["assignments"][0]
    edited = service.patch_assignment(
        created["id"],
        assignment["id"],
        AssignmentPatch(expected_version=2, position="Guichê Fictício"),
    )
    assert edited["status"] == "draft"
    second = service.publish(created["id"], PublishInput(expected_version=3, confirmed=True))
    assert second["number"] == 2
    assert service.revision(created["id"], 1)["snapshot"] == first["snapshot"]
    with pytest.raises(AuthError) as error:
        service.publish(created["id"], PublishInput(expected_version=3, confirmed=True))
    assert error.value.status == 409


@pytest.mark.integration
def test_schedule_removal_keeps_explicit_state_and_requires_reason(db_session):
    prepare(db_session)
    service = ScheduleService(db_session)
    created = service.create(ScheduleCreate(week_start="2026-11-23"))
    day = created["days"][0]
    with pytest.raises(AuthError) as error:
        service.patch_day(
            created["id"], day["id"], DayPatch(expected_version=1, state="non_working")
        )
    assert error.value.status == 409
    removed = service.remove_assignment(
        created["id"], day["assignments"][0]["id"], VersionInput(expected_version=1)
    )
    assert removed["days"][0]["state"] == "working"
    assert "missing_assignment" in {item["code"] for item in removed["diagnostics"]["errors"]}
    resolved = service.patch_day(
        created["id"],
        day["id"],
        DayPatch(
            expected_version=2, state="excluded", resolution_note="Decisão operacional fictícia"
        ),
    )
    assert not resolved["diagnostics"]["errors"]
    assert resolved["days"][0]["resolution_note"] == "Decisão operacional fictícia"


@pytest.mark.integration
def test_pending_days_and_inactive_links_block_publication(db_session):
    EmployeeService(db_session).create(EmployeeCreate(display_name="Fictícia Pendente"))
    service = ScheduleService(db_session)
    created = service.create(ScheduleCreate(week_start="2026-11-23"))
    assert len(created["diagnostics"]["errors"]) == 7
    with pytest.raises(AuthError) as error:
        service.publish(created["id"], PublishInput(expected_version=1, confirmed=True))
    assert error.value.status == 409
    unit, _ = prepare(db_session)
    next_week = service.create(ScheduleCreate(week_start="2026-11-30"))
    unit.active = False
    db_session.commit()
    assert "inactive_unit" in {
        item["code"] for item in service.detail(next_week["id"])["diagnostics"]["errors"]
    }


@pytest.fixture
def schedules_client(db_session):
    app = create_app(Settings(_env_file=None))
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[require_auth] = lambda: {"username": "fictional"}
    with TestClient(app) as client:
        yield client


@pytest.mark.integration
def test_schedule_api_guards_scope_and_validation(schedules_client):
    client = schedules_client
    headers = {"Origin": "http://localhost:3000", "X-RecepHub-CSRF": "1"}
    url = "/api/v1/schedules"
    assert client.post(url, json={"week_start": "2026-11-23"}).status_code == 403
    assert client.post(url, headers=headers, json={"week_start": "2026-11-24"}).status_code == 422
    response = client.post(url, headers=headers, json={"week_start": "2026-11-23"})
    assert response.status_code == 201
    assert response.headers["cache-control"] == "no-store"
    assert client.get(url).json()["total"] == 1
    assert client.get(url, params={"unknown": "x"}).status_code == 422
    assert client.get(f"{url}/{uuid4()}").status_code == 404
    path = f"{url}/{response.json()['id']}"
    assert (
        client.post(
            f"{path}/publish", headers=headers, json={"expected_version": 1, "confirmed": False}
        ).status_code
        == 422
    )
    assert client.delete(path).status_code == 405
