from concurrent.futures import ThreadPoolExecutor
from datetime import date, time
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.employee_work_pattern import EmployeeWorkPattern
from app.models.schedule import Schedule, ScheduleEmployeeDay
from app.models.unit import Unit
from app.schemas.schedules import AssignmentPatch, ScheduleCreate
from app.services.auth import AuthError
from app.services.schedules import ScheduleService


@pytest.mark.integration
def test_two_connections_cannot_overwrite_same_schedule_version(migrated_database):
    engine = migrated_database
    employee_id, unit_id = uuid4(), uuid4()
    schedule_id = None
    # A far-future fictional week avoids collisions with the ordinary fixture scenarios.
    # Select an unused Monday before creating records; never reuse another test's schedule.
    with Session(engine) as db:
        occupied = set(db.scalars(select(Schedule.week_start)))
    week_start = next(
        value
        for year in range(2200, 2300)
        if (value := date(year, 1, 1)).weekday() == 0 and value not in occupied
    )
    try:
        with Session(engine) as db:
            db.add(Unit(id=unit_id, name="Unidade ficticia concorrencia"))
            db.flush()
            db.add(
                Employee(
                    id=employee_id,
                    display_name="Pessoa ficticia concorrencia",
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
                        end_time=time(16) if weekday == 0 else None,
                    )
                    for weekday in range(7)
                ]
            )
            db.commit()
            detail = ScheduleService(db).create(ScheduleCreate(week_start=week_start))
            schedule_id = detail["id"]
            day = next(
                day
                for day in detail["days"]
                if day["employee_id"] == employee_id and day["work_date"] == week_start
            )
            assignment_id = day["assignments"][0]["id"]
            expected_version = detail["version"]
            # detail() starts a read transaction after create() commits. Release every
            # setup transaction before either independent connection acquires its lock.
            db.commit()

        barrier = Barrier(2, timeout=10)

        def edit(position):
            with Session(engine) as db:
                barrier.wait()
                try:
                    changed = ScheduleService(db).patch_assignment(
                        schedule_id,
                        assignment_id,
                        AssignmentPatch(expected_version=expected_version, position=position),
                    )
                    return 200, changed
                except AuthError as error:
                    db.rollback()
                    return error.status, None

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(edit, value) for value in ("Guiche A", "Guiche B")]
            results = [future.result(timeout=20) for future in futures]
        assert sorted(status for status, _ in results) == [200, 409]
        with Session(engine) as db:
            final = ScheduleService(db).detail(schedule_id)
            assert final["version"] == expected_version + 1
            saved_day = next(
                day
                for day in final["days"]
                if day["employee_id"] == employee_id and day["work_date"] == week_start
            )
            winner = next(payload for status, payload in results if status == 200)
            winner_day = next(row for row in winner["days"] if row["id"] == saved_day["id"])
            assert saved_day["assignments"] == winner_day["assignments"]
    finally:
        with Session(engine) as db:
            # All deletes target only identifiers allocated by this test. Published
            # revisions are never created, so the immutable-history trigger stays intact.
            if schedule_id is not None:
                db.execute(delete(Schedule).where(Schedule.id == schedule_id))
            else:
                # create() might commit and then fail in detail(); recover only a
                # schedule containing this test's uniquely allocated employee.
                owned = select(ScheduleEmployeeDay.schedule_id).where(
                    ScheduleEmployeeDay.employee_id == employee_id
                )
                db.execute(delete(Schedule).where(Schedule.id.in_(owned)))
            db.execute(delete(Employee).where(Employee.id == employee_id))
            db.execute(delete(Unit).where(Unit.id == unit_id))
            db.commit()
