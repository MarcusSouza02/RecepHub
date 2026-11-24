from sqlalchemy import select

from app.models.employee import Employee
from app.models.employee_work_pattern import EmployeeWorkPattern
from app.repositories.work_patterns import WorkPatternRepository
from app.schemas.work_patterns import TIME_FIELDS, WorkPatternDay
from app.services.auth import AuthError


def create_initial_pattern(db, employee):
    db.add_all(
        [
            EmployeeWorkPattern(employee_id=employee.id, weekday=day, state="pending")
            for day in range(7)
        ]
    )


def representation(employee_id, rows):
    days = []
    for row in rows:
        day = WorkPatternDay.model_validate(
            {name: getattr(row, name) for name in ("weekday", "state", *TIME_FIELDS)}
        )
        days.append(
            {
                **day.model_dump(),
                "duration_minutes": day.duration_minutes,
                "is_complete": day.is_complete,
            }
        )
    complete = len(days) == 7 and all(day["is_complete"] for day in days)
    subtotal = sum(day["duration_minutes"] or 0 for day in days)
    return {
        "employee_id": employee_id,
        "days": days,
        "subtotal_minutes": subtotal,
        "total_minutes": subtotal if complete else None,
        "is_complete": complete,
    }


class WorkPatternService:
    def __init__(self, db):
        self.db = db
        self.repository = WorkPatternRepository(db)

    def require_employee(self, employee_id, *, lock=False):
        query = select(Employee).where(Employee.id == employee_id)
        if lock:
            query = query.with_for_update()
        if self.db.scalar(query) is None:
            raise AuthError(404, "Colaboradora não encontrada")

    def get(self, employee_id):
        self.require_employee(employee_id)
        return representation(employee_id, self.repository.list(employee_id))

    def put(self, employee_id, payload):
        self.require_employee(employee_id, lock=True)
        rows = {row.weekday: row for row in self.repository.list(employee_id)}
        for day in payload.days:
            row = rows.get(day.weekday)
            if row is None:
                row = EmployeeWorkPattern(employee_id=employee_id, weekday=day.weekday)
                self.db.add(row)
            for name, value in day.model_dump().items():
                setattr(row, name, value)
        self.db.commit()
        return self.get(employee_id)
