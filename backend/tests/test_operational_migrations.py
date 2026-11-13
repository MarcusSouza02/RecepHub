from datetime import time
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from alembic import command
from app.models.employee import Employee
from app.models.employee_work_pattern import EmployeeWorkPattern
from tests.database import migration_config

pytestmark = pytest.mark.integration


def test_existing_employees_receive_seven_pending_days_on_upgrade(migrated_database):
    with migrated_database.connect() as connection:
        transaction = connection.begin()
        try:
            config = migration_config(connection)
            command.downgrade(config, "0003_employees")
            employees = [uuid4(), uuid4()]
            connection.execute(
                Employee.__table__.insert(),
                [
                    {"id": employee_id, "display_name": "Pessoa fictícia anterior à migração"}
                    for employee_id in employees
                ],
            )
            command.upgrade(config, "head")
            rows = connection.execute(select(EmployeeWorkPattern.__table__)).mappings().all()
            assert len(rows) == 14
            for employee_id in employees:
                days = [row for row in rows if row["employee_id"] == employee_id]
                assert {row["weekday"] for row in days} == set(range(7))
                assert {row["state"] for row in days} == {"pending"}
                for row in days:
                    assert all(
                        row[field] is None
                        for field in (
                            "start_time",
                            "end_time",
                            "break_start_time",
                            "break_end_time",
                        )
                    )
        finally:
            transaction.rollback()


@pytest.mark.parametrize(
    "changes",
    [
        {"weekday": 7},
        {"state": "unknown"},
        {"state": "pending", "start_time": time(8)},
        {"start_time": time(17), "end_time": time(8)},
        {"break_start_time": time(13), "break_end_time": time(12)},
        {"start_time": time(8), "end_time": time(17), "break_start_time": time(7)},
        {"start_time": time(8, 0, 1)},
    ],
)
def test_weekly_constraints_reject_direct_invalid_database_writes(db_session, changes):
    employee = Employee(display_name="Pessoa fictícia constraints")
    db_session.add(employee)
    db_session.flush()
    values = {"employee_id": employee.id, "weekday": 0, "state": "working", **changes}
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(EmployeeWorkPattern(**values))
        db_session.flush()
