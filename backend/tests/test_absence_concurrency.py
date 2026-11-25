from concurrent.futures import ThreadPoolExecutor
from datetime import date, time
from threading import Barrier, Event
from uuid import uuid4

import pytest
from sqlalchemy import delete, event, func, select
from sqlalchemy.orm import Session

from app.models.absence import Absence, AbsenceEvent
from app.models.employee import Employee
from app.models.employee_work_pattern import EmployeeWorkPattern
from app.models.schedule import Schedule, ScheduleEmployeeDay, ScheduleRevision
from app.models.unit import Unit
from app.schemas.absences import AbsenceCreate, AbsencePatch
from app.schemas.schedules import PublishInput, ScheduleCreate
from app.services.absences import AbsenceService
from app.services.auth import AuthError
from app.services.schedules import ScheduleService

pytestmark = pytest.mark.integration


def cleanup(engine, employee_id, unit_id=None):
    with Session(engine) as db:
        owned = select(ScheduleEmployeeDay.schedule_id).where(
            ScheduleEmployeeDay.employee_id == employee_id
        )
        db.execute(delete(Schedule).where(Schedule.id.in_(owned)))
        absences = select(Absence.id).where(Absence.employee_id == employee_id)
        db.execute(delete(AbsenceEvent).where(AbsenceEvent.absence_id.in_(absences)))
        db.execute(delete(Absence).where(Absence.employee_id == employee_id))
        db.execute(delete(Employee).where(Employee.id == employee_id))
        if unit_id is not None:
            db.execute(delete(Unit).where(Unit.id == unit_id))
        db.commit()


def payload(employee_id, work_date):
    return AbsenceCreate(
        employee_id=employee_id,
        type="other",
        mode="full_day",
        start_date=work_date,
        end_date=work_date,
    )


def test_two_connections_cannot_overwrite_same_absence_version(migrated_database):
    engine = migrated_database
    employee_id = uuid4()
    try:
        with Session(engine) as db:
            db.add(Employee(id=employee_id, display_name="Pessoa fictícia ausência concorrente"))
            db.commit()
            created = AbsenceService(db).create(payload(employee_id, date(2260, 1, 1)))
            absence_id = created["id"]
            db.commit()
        barrier = Barrier(2, timeout=10)

        def edit(notes):
            with Session(engine) as db:
                barrier.wait()
                try:
                    return 200, AbsenceService(db).patch(
                        absence_id,
                        AbsencePatch(expected_version=1, notes=notes),
                    )
                except AuthError as error:
                    db.rollback()
                    return error.status, None

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(edit, value) for value in ("Texto A", "Texto B")]
            results = [future.result(timeout=20) for future in futures]
        assert sorted(status for status, _ in results) == [200, 409]
        winner = next(row for status, row in results if status == 200)
        with Session(engine) as db:
            saved = AbsenceService(db).detail(absence_id)
            assert saved["version"] == 2 and saved["notes"] == winner["notes"]
            assert (
                db.scalar(
                    select(func.count())
                    .select_from(AbsenceEvent)
                    .where(
                        AbsenceEvent.absence_id == absence_id,
                    )
                )
                == 2
            )
    finally:
        cleanup(engine, employee_id)


def test_absence_writer_commits_before_waiting_publication_rechecks_conflicts(migrated_database):
    engine = migrated_database
    employee_id, unit_id = uuid4(), uuid4()
    schedule_id = None
    employee_locked, release_writer, publisher_waiting = Event(), Event(), Event()
    try:
        with Session(engine) as db:
            occupied = set(db.scalars(select(Schedule.week_start)))
            monday = next(
                value
                for year in range(2300, 2400)
                if (value := date(year, 1, 1)).weekday() == 0 and value not in occupied
            )
            db.add(Unit(id=unit_id, name="Unidade fictícia ordem de locks"))
            db.flush()
            db.add(
                Employee(
                    id=employee_id,
                    display_name="Pessoa fictícia ordem de locks",
                    home_unit_id=unit_id,
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
                        end_time=time(12) if weekday == 0 else None,
                    )
                    for weekday in range(7)
                ]
            )
            db.commit()
            detail = ScheduleService(db).create(ScheduleCreate(week_start=monday))
            schedule_id = detail["id"]
            db.commit()

        def writer():
            with Session(engine) as db:
                db.scalar(select(Employee).where(Employee.id == employee_id).with_for_update())
                employee_locked.set()
                assert release_writer.wait(10), "Publicador não alcançou o lock de colaboradora"
                return AbsenceService(db).create(payload(employee_id, monday))

        def publisher():
            assert employee_locked.wait(10)
            with engine.connect() as connection:

                def observe(conn, cursor, statement, parameters, context, executemany):
                    if "FROM employees" in statement and "FOR UPDATE" in statement:
                        publisher_waiting.set()

                event.listen(connection, "before_cursor_execute", observe)
                try:
                    with Session(bind=connection) as db:
                        try:
                            ScheduleService(db).publish(
                                schedule_id,
                                PublishInput(
                                    expected_version=1,
                                    confirmed=True,
                                ),
                            )
                            return 200
                        except AuthError as error:
                            db.rollback()
                            return error.status
                finally:
                    event.remove(connection, "before_cursor_execute", observe)

        with ThreadPoolExecutor(max_workers=2) as executor:
            write_future = executor.submit(writer)
            publish_future = executor.submit(publisher)
            try:
                assert publisher_waiting.wait(10), "Publicador não consultou colaboradora com lock"
                assert not publish_future.done()
            finally:
                release_writer.set()
            assert write_future.result(timeout=20)["status"] == "active"
            assert publish_future.result(timeout=20) == 409
        with Session(engine) as db:
            saved = db.get(Schedule, schedule_id)
            assert (saved.status, saved.version, saved.latest_revision_number) == ("draft", 1, 0)
            assert (
                db.scalar(
                    select(func.count())
                    .select_from(ScheduleRevision)
                    .where(
                        ScheduleRevision.schedule_id == schedule_id,
                    )
                )
                == 0
            )
    finally:
        release_writer.set()
        cleanup(engine, employee_id, unit_id)
