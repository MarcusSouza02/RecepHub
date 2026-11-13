from datetime import time
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.employee import Employee
from app.schemas.work_patterns import WorkPatternDay, WorkPatternPut
from app.services.auth import AuthError
from app.services.work_patterns import WorkPatternService, create_initial_pattern, representation


def week(**monday):
    return WorkPatternPut(
        days=[WorkPatternDay(weekday=0, **monday)]
        + [WorkPatternDay(weekday=day, state="non_working") for day in range(1, 7)]
    )


@pytest.mark.parametrize(
    "values",
    [
        {"start_time": "18:00", "end_time": "08:00"},
        {"start_time": "08:00", "end_time": "08:00"},
        {"start_time": "08:00", "break_end_time": "07:00"},
        {"end_time": "16:00", "break_start_time": "17:00"},
        {"break_start_time": "13:00", "break_end_time": "12:00"},
        {"start_time": "08:00:01"},
        {"start_time": "08:00:00.001"},
        {"start_time": "08:00+01:00"},
        {"start_time": 3600},
    ],
)
def test_invalid_known_intervals_and_precision(values):
    with pytest.raises(ValidationError):
        WorkPatternDay(weekday=0, state="working", **values)


@pytest.mark.parametrize("state", ["pending", "non_working"])
def test_non_working_states_reject_times(state):
    with pytest.raises(ValidationError):
        WorkPatternDay(weekday=0, state=state, start_time="08:00")


def test_complete_duration_and_incomplete_subtotal():
    payload = week(
        state="working",
        start_time="08:10",
        end_time="16:45",
        break_start_time="12:00",
        break_end_time="12:40",
    )
    result = representation(uuid4(), payload.days)
    assert result["total_minutes"] == result["subtotal_minutes"] == 475
    assert result["is_complete"] is True
    for values in (
        {},
        {"start_time": "08:00"},
        {"start_time": "08:00", "end_time": "16:00", "break_start_time": "12:00"},
    ):
        result = representation(uuid4(), week(state="working", **values).days)
        assert result["total_minutes"] is None
        assert result["subtotal_minutes"] == 0
        assert result["is_complete"] is False
    assert (
        WorkPatternDay(
            weekday=0, state="working", start_time=time(8), end_time=time(16)
        ).duration_minutes
        == 480
    )


def test_full_unique_week_required():
    for days in (
        [],
        [{"weekday": 0, "state": "pending"}] * 7,
        [{"weekday": day, "state": "pending"} for day in range(8)],
    ):
        with pytest.raises(ValidationError):
            WorkPatternPut(days=days)
    with pytest.raises(ValidationError):
        WorkPatternDay(weekday=True, state="pending")


@pytest.mark.integration
def test_pattern_initialization_atomic_replace_and_missing_employee(db_session):
    employee = Employee(display_name="Pessoa Fictícia")
    db_session.add(employee)
    db_session.flush()
    create_initial_pattern(db_session, employee)
    db_session.commit()
    service = WorkPatternService(db_session)
    initial = service.get(employee.id)
    assert len(initial["days"]) == 7
    assert all(day["state"] == "pending" for day in initial["days"])
    assert initial["total_minutes"] is None
    changed = service.put(employee.id, week(state="working", start_time="08:00", end_time="16:00"))
    assert changed["total_minutes"] == 480
    assert service.put(employee.id, week(state="pending"))["total_minutes"] is None
    assert service.get(employee.id)["days"][0]["start_time"] is None
    with pytest.raises(AuthError) as error:
        service.get(uuid4())
    assert error.value.status == 404
