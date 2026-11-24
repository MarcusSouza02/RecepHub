from sqlalchemy import select

from app.models.employee_work_pattern import EmployeeWorkPattern


class WorkPatternRepository:
    def __init__(self, db):
        self.db = db

    def list(self, employee_id):
        return list(
            self.db.scalars(
                select(EmployeeWorkPattern)
                .where(EmployeeWorkPattern.employee_id == employee_id)
                .order_by(EmployeeWorkPattern.weekday)
            )
        )
