from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.api.v1.auth import require_auth
from app.api.v1.operational_alerts import AlertPeriod, operational_alerts, router
from app.core.config import Settings
from app.main import create_app


def application(authenticated=False):
    app = create_app(Settings(_env_file=None))
    app.include_router(router, prefix="/api/v1")
    if authenticated:
        app.dependency_overrides[require_auth] = lambda: {"username": "fictional"}
    return app


def test_alerts_require_session_and_no_store():
    with TestClient(application()) as client:
        response = client.get("/api/v1/dashboard/operational-alerts")
    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "query",
    [
        "",
        "from_date=2026-11-23",
        "from_date=2026-11-24&to_date=2026-11-23",
        "from_date=2026-11-01&to_date=2026-12-02",
        "from_date=2026-11-23&to_date=2026-11-24&unexpected=1",
        "from_date=2026-11-23&from_date=2026-11-24&to_date=2026-11-24",
    ],
)
def test_alert_period_is_required_bounded_and_strict(query):
    with TestClient(application(True)) as client:
        response = client.get(f"/api/v1/dashboard/operational-alerts?{query}")
    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.integration
def test_alert_counts_are_distinct_and_pause_is_not_work(db_session):
    from app.models.absence import Absence
    from app.models.employee import Employee
    from app.models.schedule import Schedule, ScheduleAssignment, ScheduleEmployeeDay
    from app.models.unit import Unit

    employee = Employee(display_name="Pessoa fictícia alertas")
    unit = Unit(name="Unidade fictícia alertas")
    schedule = Schedule(week_start=date(2026, 11, 23))
    db_session.add_all([employee, unit, schedule])
    db_session.flush()
    day = ScheduleEmployeeDay(
        schedule_id=schedule.id,
        employee_id=employee.id,
        work_date=date(2026, 11, 23),
        state="working",
        employee_name_snapshot="Nome congelado",
        source_data={},
    )
    db_session.add(day)
    db_session.flush()
    assignment = ScheduleAssignment(
        day_id=day.id,
        unit_id=unit.id,
        unit_name_snapshot=unit.name,
        start_time=time(8),
        end_time=time(17),
        break_start_time=time(12),
        break_end_time=time(13),
    )
    pause = Absence(
        employee_id=employee.id,
        type="other",
        mode="partial",
        start_date=day.work_date,
        end_date=day.work_date,
        start_time=time(12),
        end_time=time(13),
    )
    db_session.add_all([assignment, pause])
    db_session.flush()
    period = AlertPeriod(from_date=day.work_date, to_date=day.work_date)
    result = operational_alerts(db_session, period)
    assert result["active_absences"]["total"] == 1
    assert result["current_assignment_conflicts"]["total"] == 0
    for _ in range(21):
        db_session.add(
            Absence(
                employee_id=employee.id,
                type="vacation",
                mode="full_day",
                start_date=day.work_date,
                end_date=day.work_date,
            )
        )
    db_session.flush()
    result = operational_alerts(db_session, period)
    assert result["active_absences"]["total"] == 22
    assert result["active_absences"]["truncated"] is True
    assert len(result["active_absences"]["items"]) == 20
    conflicts = result["current_assignment_conflicts"]
    assert conflicts["total"] == 1
    assert len(conflicts["items"][0]["absence_ids"]) == 21
    assert conflicts["items"][0]["href"] == f"/schedules/{schedule.id}"
    outside = operational_alerts(
        db_session, AlertPeriod(from_date=date(2026, 11, 24), to_date=date(2026, 11, 24))
    )
    assert outside["active_absences"]["total"] == 0
    assert outside["current_assignment_conflicts"]["total"] == 0
    # A complete pause covering the entire period leaves no actual work segment.
    assignment.break_start_time = assignment.start_time
    assignment.break_end_time = assignment.end_time
    db_session.flush()
    empty_work = operational_alerts(db_session, period)
    assert empty_work["active_absences"]["total"] == 22
    assert empty_work["current_assignment_conflicts"]["total"] == 0
    assert empty_work["current_assignment_conflicts"]["items"] == []
