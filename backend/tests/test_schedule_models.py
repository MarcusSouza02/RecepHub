from datetime import date, time

import pytest
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError

from app.models.employee import Employee
from app.models.schedule import Schedule, ScheduleAssignment, ScheduleEmployeeDay, ScheduleRevision
from app.models.unit import Unit


def test_schedule_metadata_preserves_references_and_snapshots():
    assert Schedule.__table__.c.week_start.unique
    assert next(iter(ScheduleAssignment.__table__.c.day_id.foreign_keys)).ondelete == "CASCADE"


@pytest.mark.integration
def test_schedule_defaults_and_unique_monday(db_session):
    schedule = Schedule(week_start=date(2026, 11, 23))
    db_session.add(schedule)
    db_session.flush()
    assert (schedule.status, schedule.version, schedule.latest_revision_number) == ("draft", 1, 0)
    for values in (
        {"week_start": date(2026, 11, 24)},
        {"week_start": date(2026, 11, 23)},
        {"week_start": date(2026, 11, 30), "version": 0},
        {"week_start": date(2026, 11, 30), "status": "invalid"},
    ):
        with pytest.raises(IntegrityError), db_session.begin_nested():
            db_session.add(Schedule(**values))
            db_session.flush()


@pytest.fixture
def scheduled_day(db_session):
    employee = Employee(display_name="Pessoa de teste")
    unit = Unit(name="Unidade de teste")
    schedule = Schedule(week_start=date(2026, 11, 23))
    db_session.add_all([employee, unit, schedule])
    db_session.flush()
    day = ScheduleEmployeeDay(
        schedule_id=schedule.id,
        employee_id=employee.id,
        work_date=schedule.week_start,
        state="working",
        employee_name_snapshot=employee.display_name,
        source_data={"state": "working"},
    )
    db_session.add(day)
    db_session.flush()
    return schedule, day, unit


@pytest.mark.integration
@pytest.mark.parametrize(
    "values",
    [
        {"start_time": time(17), "end_time": time(8)},
        {"start_time": time(8, 0, 1)},
        {"break_start_time": time(12)},
        {"break_start_time": time(7), "break_end_time": time(9)},
        {"break_start_time": time(13), "break_end_time": time(12)},
    ],
)
def test_assignment_rejects_invalid_times(db_session, scheduled_day, values):
    _, day, unit = scheduled_day
    fields = dict(
        day_id=day.id,
        unit_id=unit.id,
        unit_name_snapshot=unit.name,
        start_time=time(8),
        end_time=time(17),
    )
    fields.update(values)
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(ScheduleAssignment(**fields))
        db_session.flush()


@pytest.mark.integration
def test_exclusion_requires_reason_and_revisions_are_immutable(db_session, scheduled_day):
    schedule, day, _ = scheduled_day
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.execute(
            update(ScheduleEmployeeDay)
            .where(ScheduleEmployeeDay.id == day.id)
            .values(state="excluded", resolution_note="   ")
        )
    revision = ScheduleRevision(
        schedule_id=schedule.id, number=1, source_version=1, snapshot={"employee": "Nome congelado"}
    )
    db_session.add(revision)
    db_session.flush()
    for statement in (
        update(ScheduleRevision).where(ScheduleRevision.id == revision.id).values(snapshot={}),
        delete(ScheduleRevision).where(ScheduleRevision.id == revision.id),
        delete(Schedule).where(Schedule.id == schedule.id),
    ):
        with pytest.raises(IntegrityError), db_session.begin_nested():
            db_session.execute(statement)
    db_session.refresh(revision)
    assert revision.snapshot == {"employee": "Nome congelado"}
