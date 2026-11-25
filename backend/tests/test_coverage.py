from datetime import date, time
from types import SimpleNamespace as Row
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.coverage import CoverageConfirm, CoveragePreview
from app.services.absence_conflicts import absence_intersects, work_segments
from app.services.coverage import CoverageService


def payload(**changes):
    return CoveragePreview(
        **{
            "expected_version": 1,
            "work_date": "2026-11-23",
            "unit_id": uuid4(),
            "start_time": "09:00",
            "end_time": "10:00",
            **changes,
        }
    )


def candidate_data():
    employee = Row(id=uuid4(), active=True, display_name="Pessoa fictícia")
    day = Row(
        state="working",
        employee_name_snapshot="Nome congelado",
        source_data={
            "weekday": 0,
            "state": "working",
            "start_time": "08:00",
            "end_time": "17:00",
            "break_start_time": "12:00",
            "break_end_time": "13:00",
        },
    )
    return employee, day, Row(active=True)


def test_candidate_uses_frozen_work_segments_and_treats_pause_as_unknown_availability():
    employee, day, unit = candidate_data()
    service = CoverageService(None)
    result = service.candidate(employee, day, [], [], unit, payload())
    assert result["classification"] == "available"
    assert result["employee_name"] == "Nome congelado"
    assert len(result["known_periods"]) == 2
    crossing = service.candidate(employee, day, [], [], unit, payload(end_time="14:00"))
    assert crossing["classification"] == "unavailable"
    assert crossing["reasons"][0]["code"] == "outside_pattern"


def test_missing_day_or_pending_source_never_implies_availability():
    employee, day, unit = candidate_data()
    service = CoverageService(None)
    assert service.candidate(employee, None, [], [], unit, payload())["classification"] == (
        "insufficient_information"
    )
    day.source_data["state"] = "pending"
    day.source_data.update(
        start_time=None, end_time=None, break_start_time=None, break_end_time=None
    )
    assert service.candidate(employee, day, [], [], unit, payload())["classification"] == (
        "insufficient_information"
    )


def test_missing_day_with_known_absence_is_unavailable():
    employee, _, unit = candidate_data()
    absence = Row(
        employee_id=employee.id,
        status="active",
        mode="full_day",
        start_date=date(2026, 11, 23),
        end_date=date(2026, 11, 23),
    )
    result = CoverageService(None).candidate(employee, None, [], [absence], unit, payload())
    assert result["classification"] == "unavailable"
    assert {reason["code"] for reason in result["reasons"]} == {"missing_day", "absence_conflict"}


def test_existing_outside_pattern_counts_against_known_duration():
    employee, day, unit = candidate_data()
    assignments = [
        Row(start_time=time(17), end_time=time(21)),
        Row(start_time=time(8), end_time=time(12)),
    ]
    result = CoverageService(None).candidate(
        employee,
        day,
        assignments,
        [],
        unit,
        payload(start_time="13:00", end_time="17:00"),
    )
    assert result["classification"] == "unavailable"
    assert {reason["code"] for reason in result["reasons"]} == {"exceeds_known_duration"}


def test_whole_assignment_occupies_pause_and_adjacency_is_allowed():
    employee, day, unit = candidate_data()
    assignment = Row(start_time=time(8), end_time=time(9))
    service = CoverageService(None)
    assert (
        service.candidate(employee, day, [assignment], [], unit, payload())["classification"]
        == "available"
    )
    assignment.end_time = time(10)
    assert (
        service.candidate(employee, day, [assignment], [], unit, payload())["classification"]
        == "unavailable"
    )


def test_absence_inside_pause_does_not_conflict_with_actual_work():
    absence = Row(
        status="active",
        mode="partial",
        start_date=date(2026, 11, 23),
        end_date=date(2026, 11, 23),
        start_time=time(12),
        end_time=time(13),
    )
    segments = work_segments(time(8), time(17), time(12), time(13))
    assert not absence_intersects(absence, date(2026, 11, 23), segments)
    absence.start_time = time(11, 59)
    assert absence_intersects(absence, date(2026, 11, 23), segments)
    absence.status = "cancelled"
    assert not absence_intersects(absence, date(2026, 11, 23), segments)


@pytest.mark.parametrize(
    "changes",
    [
        {"start_time": 3600},
        {"start_time": "09:00:01"},
        {"start_time": "09:00+01:00"},
        {"end_time": "09:00"},
        {"expected_version": True},
    ],
)
def test_coverage_rejects_ambiguous_times_and_versions(changes):
    with pytest.raises(ValidationError):
        payload(**changes)


@pytest.mark.parametrize("confirmation", [False, 1, "true"])
def test_confirmation_requires_explicit_boolean(confirmation):
    with pytest.raises(ValidationError):
        CoverageConfirm(**payload().model_dump(), employee_id=uuid4(), confirmed=confirmation)


@pytest.fixture
def coverage_week(db_session):
    from app.models.employee import Employee
    from app.models.employee_work_pattern import EmployeeWorkPattern
    from app.models.unit import Unit
    from app.schemas.schedules import ScheduleCreate
    from app.services.schedules import ScheduleService

    unit = Unit(name="Destino fictício")
    employee = Employee(display_name="Cobertura fictícia")
    db_session.add_all([unit, employee])
    db_session.flush()
    for weekday in range(7):
        db_session.add(
            EmployeeWorkPattern(
                employee_id=employee.id,
                weekday=weekday,
                state="working" if weekday == 0 else "non_working",
                start_time=time(8) if weekday == 0 else None,
                end_time=time(17) if weekday == 0 else None,
            )
        )
    db_session.commit()
    detail = ScheduleService(db_session).create(ScheduleCreate(week_start=date(2026, 11, 23)))
    return CoverageService(db_session), detail, employee, unit


@pytest.mark.integration
def test_preview_has_no_side_effect_and_confirm_adds_only_draft_assignment(coverage_week):
    from app.services.auth import AuthError

    service, detail, employee, unit = coverage_week
    request = payload(unit_id=unit.id)
    preview = service.preview(detail["id"], request)
    assert preview["candidates"][0]["classification"] == "available"
    assert service.schedules.detail(detail["id"])["version"] == 1
    confirmation = CoverageConfirm(
        **request.model_dump(),
        employee_id=employee.id,
        confirmed=True,
    )
    updated = service.confirm(detail["id"], confirmation)
    assert updated["version"] == 2
    assert updated["status"] == "draft"
    assert updated["latest_revision_number"] == 0
    assert len(updated["days"][0]["assignments"]) == 1
    with pytest.raises(AuthError) as error:
        service.confirm(detail["id"], confirmation)
    assert error.value.status == 409


@pytest.mark.integration
def test_confirmation_rechecks_absence_created_after_preview(coverage_week):
    from app.models.absence import Absence
    from app.services.auth import AuthError

    service, detail, employee, unit = coverage_week
    request = payload(unit_id=unit.id)
    assert service.preview(detail["id"], request)["candidates"][0]["classification"] == "available"
    service.db.add(
        Absence(
            employee_id=employee.id,
            type="other",
            mode="full_day",
            start_date=request.work_date,
            end_date=request.work_date,
        )
    )
    service.db.commit()
    with pytest.raises(AuthError) as error:
        service.confirm(
            detail["id"],
            CoverageConfirm(
                **request.model_dump(),
                employee_id=employee.id,
                confirmed=True,
            ),
        )
    assert error.value.status == 409
    unchanged = service.schedules.detail(detail["id"])
    assert unchanged["version"] == 1
    assert not unchanged["days"][0]["assignments"]


@pytest.mark.integration
def test_overlapping_absences_produce_one_diagnostic_per_assignment(coverage_week):
    from app.models.absence import Absence
    from app.services.absence_conflicts import absence_diagnostics

    service, detail, employee, unit = coverage_week
    request = payload(unit_id=unit.id)
    service.confirm(
        detail["id"],
        CoverageConfirm(
            **request.model_dump(),
            employee_id=employee.id,
            confirmed=True,
        ),
    )
    for absence_type in ("other", "vacation"):
        service.db.add(
            Absence(
                employee_id=employee.id,
                type=absence_type,
                mode="full_day",
                start_date=request.work_date,
                end_date=request.work_date,
            )
        )
    service.db.commit()
    days, grouped = service.schedules.rows(detail["id"])
    result = absence_diagnostics(service.db, days, grouped)
    assert len(result["errors"]) == 1
    assert len(result["errors"][0]["absence_ids"]) == 2


@pytest.mark.parametrize("operation", ["preview", "confirm"])
def test_coverage_api_requires_session(client, operation):
    response = client.post(f"/api/v1/schedules/{uuid4()}/coverage/{operation}")
    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("operation", ["preview", "confirm"])
def test_coverage_api_guards_csrf_body_limit_and_no_store(operation):
    from fastapi.testclient import TestClient

    from app.api.v1.auth import require_auth
    from app.core.config import Settings
    from app.main import create_app

    app = create_app(Settings(_env_file=None))
    app.dependency_overrides[require_auth] = lambda: {"username": "fictional"}
    url = f"/api/v1/schedules/{uuid4()}/coverage/{operation}"
    with TestClient(app) as client:
        denied = client.post(url, json={})
        assert denied.status_code == 403
        assert denied.headers["cache-control"] == "no-store"
        large = client.post(
            url,
            headers={
                "Origin": "http://localhost:3000",
                "X-RecepHub-CSRF": "1",
                "Content-Type": "application/json",
            },
            content='{"position":"' + "x" * 4096 + '"}',
        )
        assert large.status_code == 413
        assert large.headers["cache-control"] == "no-store"


@pytest.mark.integration
def test_coverage_commit_failure_rolls_back_assignment_and_version(coverage_week, monkeypatch):
    from fastapi.testclient import TestClient
    from sqlalchemy.exc import OperationalError
    from sqlalchemy.orm import Session

    from app.api.v1.auth import require_auth
    from app.core.config import Settings
    from app.database.session import get_session
    from app.main import create_app

    service, detail, employee, unit = coverage_week
    app = create_app(Settings(_env_file=None))
    app.dependency_overrides[require_auth] = lambda: {"username": "fictional"}

    def session_dependency():
        with Session(bind=service.db.bind, join_transaction_mode="create_savepoint") as session:

            def failing_commit():
                session.flush()
                raise OperationalError("fictional-private-sql", {}, Exception("private"))

            monkeypatch.setattr(session, "commit", failing_commit)
            yield session

    app.dependency_overrides[get_session] = session_dependency
    confirmation = CoverageConfirm(
        **payload(unit_id=unit.id).model_dump(), employee_id=employee.id, confirmed=True
    )
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/schedules/{detail['id']}/coverage/confirm",
            headers={
                "Origin": "http://localhost:3000",
                "X-RecepHub-CSRF": "1",
            },
            json=confirmation.model_dump(mode="json"),
        )
    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    assert "fictional-private-sql" not in response.text
    service.db.expire_all()
    unchanged = service.schedules.detail(detail["id"])
    assert unchanged["version"] == 1
    assert unchanged["days"][0]["state"] == "pending"
    assert unchanged["days"][0]["assignments"] == []


@pytest.mark.integration
def test_confirm_cannot_exceed_frozen_duration_after_manual_outside_period(coverage_week):
    from sqlalchemy import select

    from app.models.schedule import ScheduleEmployeeDay
    from app.schemas.schedules import AssignmentCreate
    from app.services.auth import AuthError

    service, detail, employee, unit = coverage_week
    day = service.db.scalar(
        select(ScheduleEmployeeDay).where(
            ScheduleEmployeeDay.schedule_id == detail["id"],
            ScheduleEmployeeDay.work_date == date(2026, 11, 23),
        )
    )
    day.source_data = {**day.source_data, "break_start_time": "12:00", "break_end_time": "13:00"}
    service.db.commit()
    service.schedules.add_assignment(
        detail["id"],
        AssignmentCreate(
            expected_version=1,
            day_id=day.id,
            unit_id=unit.id,
            start_time="17:00",
            end_time="21:00",
        ),
    )
    first = service.confirm(
        detail["id"],
        CoverageConfirm(
            **payload(
                expected_version=2, unit_id=unit.id, start_time="08:00", end_time="12:00"
            ).model_dump(),
            employee_id=employee.id,
            confirmed=True,
        ),
    )
    assert first["version"] == 3
    request = payload(expected_version=3, unit_id=unit.id, start_time="13:00", end_time="17:00")
    candidate = service.preview(detail["id"], request)["candidates"][0]
    assert candidate["classification"] == "unavailable"
    assert "exceeds_known_duration" in {reason["code"] for reason in candidate["reasons"]}
    with pytest.raises(AuthError) as error:
        service.confirm(
            detail["id"],
            CoverageConfirm(
                **request.model_dump(),
                employee_id=employee.id,
                confirmed=True,
            ),
        )
    assert error.value.status == 409
    assert service.schedules.detail(detail["id"])["version"] == 3
