from datetime import UTC, date, datetime, time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from alembic import command
from app.api.v1.auth import require_auth
from app.core.config import Settings
from app.database.session import get_session
from app.main import create_app
from app.models.absence import Absence, AbsenceEvent
from app.models.employee import Employee
from app.models.employee_work_pattern import EmployeeWorkPattern
from app.models.schedule import ScheduleRevision
from app.models.unit import Unit
from app.schemas.absences import AbsenceCreate
from app.schemas.schedules import AssignmentPatch, PublishInput, ScheduleCreate
from app.services.absences import AbsenceService
from app.services.auth import AuthError
from app.services.schedules import ScheduleService
from tests.database import migration_config

pytestmark = pytest.mark.integration


def absence_values(person_id, **changes):
    return {
        "employee_id": person_id,
        "type": "vacation",
        "mode": "full_day",
        "start_date": date(2026, 11, 23),
        "end_date": date(2026, 11, 23),
        **changes,
    }


def test_absence_after_publication_blocks_next_revision_preserving_snapshot(db_session):
    unit = Unit(name="Unidade fictícia segurança")
    db_session.add(unit)
    db_session.flush()
    employee = Employee(display_name="Pessoa fictícia segurança", home_unit_id=unit.id)
    db_session.add(employee)
    db_session.flush()
    for weekday in range(7):
        db_session.add(
            EmployeeWorkPattern(
                employee_id=employee.id,
                weekday=weekday,
                state="working" if weekday == 0 else "non_working",
                start_time=time(8) if weekday == 0 else None,
                end_time=time(12) if weekday == 0 else None,
            )
        )
    db_session.commit()
    schedules = ScheduleService(db_session)
    detail = schedules.create(ScheduleCreate(week_start="2026-11-23"))
    published = schedules.publish(detail["id"], PublishInput(expected_version=1, confirmed=True))
    AbsenceService(db_session).create(AbsenceCreate(**absence_values(employee.id)))
    assert schedules.revision(detail["id"], 1)["snapshot"] == published["snapshot"]
    current = schedules.detail(detail["id"])
    edited = schedules.patch_assignment(
        detail["id"],
        current["days"][0]["assignments"][0]["id"],
        AssignmentPatch(expected_version=current["version"], position="Ajuste fictício"),
    )
    with pytest.raises(AuthError) as conflict:
        schedules.publish(
            detail["id"],
            PublishInput(
                expected_version=edited["version"],
                confirmed=True,
            ),
        )
    assert conflict.value.status == 409
    assert schedules.revision(detail["id"], 1)["snapshot"] == published["snapshot"]
    assert db_session.scalar(select(func.count()).select_from(ScheduleRevision)) == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"mode": "partial"},
        {
            "mode": "partial",
            "start_time": time(8),
            "end_time": time(9),
            "end_date": date(2026, 11, 24),
        },
        {"mode": "partial", "start_time": time(9), "end_time": time(8)},
        {"mode": "partial", "start_time": time(8, 0, 1), "end_time": time(9)},
        {"start_time": time(8)},
        {"end_date": date(2026, 11, 22)},
        {"status": "cancelled"},
        {"status": "invalid"},
        {"cancelled_at": datetime(2026, 11, 24, tzinfo=UTC)},
        {"version": 0},
        {"employee_id": uuid4()},
    ],
)
def test_database_rejects_invalid_absences(db_session, changes):
    employee = Employee(display_name="Pessoa fictícia constraints")
    db_session.add(employee)
    db_session.flush()
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(Absence(**absence_values(employee.id, **changes)))
        db_session.flush()


def test_absence_commit_failure_rolls_back_row_and_event(db_session, monkeypatch):
    employee = Employee(display_name="Pessoa fictícia rollback")
    db_session.add(employee)
    db_session.commit()
    employee_id = employee.id
    app = create_app(Settings(_env_file=None))
    app.dependency_overrides[require_auth] = lambda: {"username": "fictional"}

    def session_dependency():
        with Session(bind=db_session.connection(), join_transaction_mode="create_savepoint") as db:

            def fail_commit():
                db.flush()
                assert db.scalar(select(func.count()).select_from(AbsenceEvent)) == 1
                raise OperationalError("fictional-secret-sql", {}, Exception("private"))

            monkeypatch.setattr(db, "commit", fail_commit)
            yield db

    app.dependency_overrides[get_session] = session_dependency
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/absences",
            headers={
                "Origin": "http://localhost:3000",
                "X-RecepHub-CSRF": "1",
            },
            json={
                "employee_id": str(employee_id),
                "type": "other",
                "mode": "full_day",
                "start_date": "2026-11-23",
                "end_date": "2026-11-23",
            },
        )
    assert response.status_code == 503
    assert "fictional-secret-sql" not in response.text and "private" not in response.text
    assert db_session.scalar(select(func.count()).select_from(Absence)) == 0
    assert db_session.scalar(select(func.count()).select_from(AbsenceEvent)) == 0


def test_populated_absence_migration_round_trip_is_transactionally_isolated(migrated_database):
    with migrated_database.connect() as connection:
        transaction = connection.begin()
        try:
            employee_id, absence_id = uuid4(), uuid4()
            connection.execute(
                Employee.__table__.insert().values(
                    id=employee_id,
                    display_name="Pessoa fictícia migração",
                )
            )
            connection.execute(
                Absence.__table__.insert().values(
                    id=absence_id,
                    **absence_values(employee_id),
                )
            )
            connection.execute(
                AbsenceEvent.__table__.insert().values(
                    id=uuid4(),
                    absence_id=absence_id,
                    version=1,
                    action="created",
                    snapshot={"employee_name": "Nome fictício preservado"},
                )
            )
            assert connection.scalar(select(func.count()).select_from(AbsenceEvent)) == 1
            config = migration_config(connection)
            command.downgrade(config, "0005_schedules")
            assert not {"absences", "absence_events"} & set(inspect(connection).get_table_names())
            assert connection.scalar(select(Employee.id).where(Employee.id == employee_id))
            command.upgrade(config, "head")
            assert {"absences", "absence_events"} <= set(inspect(connection).get_table_names())
            assert connection.scalar(select(func.count()).select_from(AbsenceEvent)) == 0
            assert connection.scalar(select(func.count()).select_from(Absence)) == 0
        finally:
            transaction.rollback()
