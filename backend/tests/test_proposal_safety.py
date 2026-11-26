import time as clock
from concurrent.futures import ThreadPoolExecutor
from datetime import date, time
from threading import Barrier, Event
from uuid import uuid4

import pytest
from sqlalchemy import delete, event, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.absence import Absence, AbsenceEvent
from app.models.employee import Employee
from app.models.employee_work_pattern import EmployeeWorkPattern
from app.models.schedule import Schedule, ScheduleAssignment, ScheduleEmployeeDay
from app.models.unit import Unit
from app.schemas.absences import AbsenceCreate
from app.schemas.proposals import ProposalConfirm, ProposalPreview
from app.schemas.schedules import ScheduleCreate
from app.services.absences import AbsenceService
from app.services.ai.fake import FakeProvider
from app.services.auth import AuthError
from app.services.proposals import ProposalService
from app.services.schedules import ScheduleService

pytestmark = pytest.mark.integration


def service(db, provider=None):
    return ProposalService(
        db,
        Settings(_env_file=None, proposal_signing_key="fictional-proposal-safety-key-at-least-32"),
        "s" * 43,
        provider or FakeProvider(),
    )


def seed(db, monday, employee_id, unit_id):
    db.add(Unit(id=unit_id, name="Unidade ficticia propostas seguras"))
    db.flush()
    db.add(
        Employee(
            id=employee_id, display_name="Pessoa ficticia proposta segura", home_unit_id=unit_id
        )
    )
    db.flush()
    db.add_all(
        [
            EmployeeWorkPattern(
                employee_id=employee_id,
                weekday=weekday,
                state="working" if weekday == 0 else "non_working",
                start_time=time(8) if weekday == 0 else None,
                end_time=time(16) if weekday == 0 else None,
                break_start_time=time(12) if weekday == 0 else None,
                break_end_time=time(13) if weekday == 0 else None,
            )
            for weekday in range(7)
        ]
    )
    db.commit()
    detail = ScheduleService(db).create(ScheduleCreate(week_start=monday))
    day = next(
        row
        for row in detail["days"]
        if row["employee_id"] == employee_id and row["work_date"] == monday
    )
    db.commit()
    return detail, day


def operation(day, unit_id, start="09:00", end="12:00", action="patch"):
    return {
        "action": action,
        "day_id": str(day["id"]),
        "assignment_id": str(day["assignments"][0]["id"]) if action == "patch" else None,
        "unit_id": str(unit_id),
        "times": {
            "start_time": start,
            "end_time": end,
            "break_start_time": None,
            "break_end_time": None,
            "position": None,
        },
    }


def receipt(db, detail, operations):
    instance = service(db)
    return instance.sign(
        {
            "schedule": str(detail["id"]),
            "session": instance.session_hash,
            "version": detail["version"],
            "expires": int(clock.time()) + 600,
            "operations": operations,
        }
    )


@pytest.fixture
def proposal_data(db_session):
    detail, day = seed(db_session, date(2026, 11, 23), uuid4(), uuid4())
    return db_session, detail, day, day["assignments"][0]["unit_id"]


@pytest.mark.parametrize(
    "start,end,action,message",
    [
        ("09:00", "10:00", "add", "sobrepostos"),
        ("07:00", "16:00", "patch", "jornada conhecida"),
        ("11:00", "14:00", "patch", "jornada conhecida"),
        ("16:00", "18:00", "add", "jornada conhecida"),
    ],
)
def test_proposal_preview_rejects_overlap_extra_duration_and_frozen_pause(
    proposal_data, start, end, action, message
):
    db, detail, day, unit_id = proposal_data
    op = operation(day, unit_id, start, end, action)
    op.update(day_id="D1", assignment_id="A1" if action == "patch" else None, unit_id="U1")
    fake = FakeProvider({"status": "ready", "message": "Proposta ficticia", "operations": [op]})
    result = service(db, fake).preview(
        detail["id"],
        ProposalPreview(
            expected_version=1,
            request="Periodo ficticio explicito",
            reference_date=date(2026, 11, 23),
        ),
    )
    assert result["status"] == "blocked"
    assert result["receipt"] is None
    assert message in result["message"]
    assert db.get(Schedule, detail["id"]).version == 1
    saved = db.get(ScheduleAssignment, day["assignments"][0]["id"])
    assert (saved.start_time, saved.end_time) == (time(8), time(16))


def test_valid_first_operation_and_invalid_second_never_partially_apply(proposal_data):
    db, detail, day, unit_id = proposal_data
    operations = [
        operation(day, unit_id),
        {
            "action": "remove",
            "day_id": str(day["id"]),
            "assignment_id": str(uuid4()),
        },
    ]
    signed = receipt(db, detail, operations)
    with pytest.raises(AuthError) as error:
        service(db).confirm(detail["id"], ProposalConfirm(receipt=signed, confirmed=True))
    assert error.value.status == 409
    assert db.get(Schedule, detail["id"]).version == 1
    saved = db.get(ScheduleAssignment, day["assignments"][0]["id"])
    assert (saved.start_time, saved.end_time) == (time(8), time(16))


def cleanup(engine, employee_id, unit_id):
    with Session(engine) as db:
        owned = select(ScheduleEmployeeDay.schedule_id).where(
            ScheduleEmployeeDay.employee_id == employee_id
        )
        db.execute(delete(Schedule).where(Schedule.id.in_(owned)))
        absence_ids = select(Absence.id).where(Absence.employee_id == employee_id)
        db.execute(delete(AbsenceEvent).where(AbsenceEvent.absence_id.in_(absence_ids)))
        db.execute(delete(Absence).where(Absence.employee_id == employee_id))
        db.execute(delete(Employee).where(Employee.id == employee_id))
        db.execute(delete(Unit).where(Unit.id == unit_id))
        db.commit()


def unused_week(engine):
    with Session(engine) as db:
        occupied = set(db.scalars(select(Schedule.week_start)))
    return next(
        value
        for year in range(2400, 2500)
        if (value := date(year, 1, 1)).weekday() == 0 and value not in occupied
    )


def test_absence_writer_commits_before_waiting_proposal_confirmation(migrated_database):
    engine = migrated_database
    employee_id, unit_id = uuid4(), uuid4()
    employee_locked, confirm_waiting, release_writer = Event(), Event(), Event()
    try:
        monday = unused_week(engine)
        with Session(engine) as db:
            detail, day = seed(db, monday, employee_id, unit_id)
            signed = receipt(db, detail, [operation(day, unit_id)])
            db.commit()

        def writer():
            with Session(engine) as db:
                db.scalar(select(Employee).where(Employee.id == employee_id).with_for_update())
                employee_locked.set()
                assert release_writer.wait(10)
                return AbsenceService(db).create(
                    AbsenceCreate(
                        employee_id=employee_id,
                        type="day_off",
                        mode="full_day",
                        start_date=monday,
                        end_date=monday,
                    )
                )

        def confirmer():
            assert employee_locked.wait(10)
            with engine.connect() as connection:

                def observe(conn, cursor, statement, parameters, context, executemany):
                    if "FROM employees" in statement and "FOR UPDATE" in statement:
                        confirm_waiting.set()

                event.listen(connection, "before_cursor_execute", observe)
                try:
                    with Session(bind=connection) as db:
                        try:
                            service(db).confirm(
                                detail["id"], ProposalConfirm(receipt=signed, confirmed=True)
                            )
                            return 200
                        except AuthError as error:
                            return error.status
                finally:
                    event.remove(connection, "before_cursor_execute", observe)

        with ThreadPoolExecutor(max_workers=2) as executor:
            write_future = executor.submit(writer)
            confirm_future = executor.submit(confirmer)
            try:
                assert confirm_waiting.wait(10)
                assert not confirm_future.done()
            finally:
                release_writer.set()
            assert write_future.result(timeout=20)["status"] == "active"
            assert confirm_future.result(timeout=20) == 409
        with Session(engine) as db:
            assert db.get(Schedule, detail["id"]).version == 1
            saved = db.get(ScheduleAssignment, day["assignments"][0]["id"])
            assert (saved.start_time, saved.end_time) == (time(8), time(16))
    finally:
        release_writer.set()
        cleanup(engine, employee_id, unit_id)


def test_concurrent_confirmation_replay_changes_version_once(migrated_database):
    engine = migrated_database
    employee_id, unit_id = uuid4(), uuid4()
    try:
        with Session(engine) as db:
            detail, day = seed(db, unused_week(engine), employee_id, unit_id)
            signed = receipt(db, detail, [operation(day, unit_id)])
            db.commit()
        barrier = Barrier(2, timeout=10)

        def confirm_once():
            with Session(engine) as db:
                barrier.wait()
                try:
                    service(db).confirm(
                        detail["id"], ProposalConfirm(receipt=signed, confirmed=True)
                    )
                    return 200
                except AuthError as error:
                    return error.status

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(confirm_once) for _ in range(2)]
            assert sorted(future.result(timeout=20) for future in futures) == [200, 409]
        with Session(engine) as db:
            assert db.get(Schedule, detail["id"]).version == 2
            saved = db.get(ScheduleAssignment, day["assignments"][0]["id"])
            assert (saved.start_time, saved.end_time) == (time(9), time(12))
    finally:
        cleanup(engine, employee_id, unit_id)
