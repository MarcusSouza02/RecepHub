from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select

from app.api.v1.absences import router
from app.core.config import Settings
from app.main import create_app
from app.models.absence import AbsenceEvent
from app.models.employee import Employee
from app.schemas.absences import AbsenceCancel, AbsenceCreate, AbsencePatch, AbsenceQuery
from app.services.absences import AbsenceService, periods_overlap
from app.services.auth import AuthError


def create_input(**changes):
    return AbsenceCreate.model_validate(
        {
            "employee_id": uuid4(),
            "type": "vacation",
            "mode": "full_day",
            "start_date": "2026-11-24",
            "end_date": "2026-11-25",
            **changes,
        }
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"end_date": "2026-11-23"},
        {"start_time": "08:00"},
        {"mode": "partial"},
        {"mode": "partial", "start_time": "08:00", "end_time": "09:00"},
        {"mode": "partial", "end_date": "2026-11-24", "start_time": "09:00", "end_time": "08:00"},
        {
            "mode": "partial",
            "end_date": "2026-11-24",
            "start_time": "08:00:01",
            "end_time": "09:00",
        },
        {"mode": "partial", "end_date": "2026-11-24", "start_time": "08:00Z", "end_time": "09:00Z"},
        {"mode": "partial", "end_date": "2026-11-24", "start_time": 3600, "end_time": "09:00"},
        {"notes": "x" * 501},
        {"status": "cancelled"},
        {"type": "invalid"},
    ],
)
def test_absence_invalid_periods(changes):
    with pytest.raises(ValidationError):
        create_input(**changes)


def test_absence_version_confirmation_patch_and_query():
    for values in (
        {"expected_version": True, "notes": "a"},
        {"expected_version": 1},
        {"expected_version": 1, "employee_id": str(uuid4())},
        {"expected_version": 1, "type": None},
    ):
        with pytest.raises(ValidationError):
            AbsencePatch(**values)
    for confirmation in (False, 1, "true"):
        with pytest.raises(ValidationError):
            AbsenceCancel(expected_version=1, confirmed=confirmation)
    for values in (
        {"page_size": 101},
        {"status": "inactive"},
        {"unknown": 1},
        {"from_date": "2026-12-01", "to_date": "2026-11-01"},
    ):
        with pytest.raises(ValidationError):
            AbsenceQuery(**values)
    assert create_input().start_date == date(2026, 11, 24)


def test_overlap_boundaries():
    left = create_input(mode="partial", end_date="2026-11-24", start_time="08:00", end_time="10:00")
    adjacent = left.model_copy(update={"start_time": left.end_time})
    assert not periods_overlap(left, adjacent)
    assert periods_overlap(left, create_input())
    assert not periods_overlap(left, create_input(start_date="2026-11-25"))


def test_all_absence_routes_require_authentication():
    app = create_app(Settings(_env_file=None))
    app.include_router(router, prefix="/api/v1")
    with TestClient(app) as client:
        for method, suffix in (
            ("get", ""),
            ("post", ""),
            ("get", f"/{uuid4()}"),
            ("patch", f"/{uuid4()}"),
            ("post", f"/{uuid4()}/cancel"),
            ("get", f"/{uuid4()}/events"),
        ):
            assert getattr(client, method)(f"/api/v1/absences{suffix}").status_code == 401


def test_absence_history_versioning_and_cancellation(db_session):
    employee = Employee(display_name="Pessoa fictícia", active=False)
    db_session.add(employee)
    db_session.flush()
    service = AbsenceService(db_session)
    first = service.create(create_input(employee_id=employee.id))
    second = service.create(create_input(employee_id=employee.id))
    assert second["overlap_ids"] == [first["id"]]
    assert service.detail(first["id"])["overlap_warning"]
    changed = service.patch(first["id"], AbsencePatch(expected_version=1, notes="Ajuste"))
    assert changed["version"] == 2
    with pytest.raises(AuthError) as conflict:
        service.patch(first["id"], AbsencePatch(expected_version=1, notes="Antigo"))
    assert conflict.value.status == 409
    cancelled = service.cancel(first["id"], AbsenceCancel(expected_version=2, confirmed=True))
    assert cancelled["version"] == 3 and not cancelled["overlap_warning"]
    repeated = service.cancel(first["id"], AbsenceCancel(expected_version=2, confirmed=True))
    assert repeated == cancelled
    events = service.events(first["id"])["items"]
    assert [event["action"] for event in events] == ["created", "updated", "cancelled"]
    assert events[0]["snapshot"]["notes"] is None
    assert events[1]["snapshot"]["notes"] == "Ajuste"
    assert (
        db_session.scalar(
            select(AbsenceEvent).where(
                AbsenceEvent.absence_id == first["id"], AbsenceEvent.version == 3
            )
        )
        is not None
    )


def test_merge_period_validation_precedes_mutation(db_session):
    employee = Employee(display_name="Teste fictício")
    db_session.add(employee)
    db_session.flush()
    service = AbsenceService(db_session)
    row = service.create(create_input(employee_id=employee.id))
    with pytest.raises(AuthError) as invalid:
        service.patch(row["id"], AbsencePatch(expected_version=1, mode="partial"))
    assert invalid.value.status == 422
    assert service.detail(row["id"])["version"] == 1
