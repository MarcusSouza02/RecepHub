from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.models.employee import Employee


class EmployeeRepository:
    def __init__(self, db):
        self.db = db

    def get(self, employee_id, *, lock=False):
        query = select(Employee).where(Employee.id == employee_id)
        if lock:
            query = query.with_for_update()
        else:
            query = query.options(joinedload(Employee.home_unit))
        return self.db.scalar(query)

    def list(self, filters):
        clauses = []
        if filters.status != "all":
            clauses.append(Employee.active.is_(filters.status == "active"))
        if filters.q and filters.q.strip():
            # Escape wildcards: the search is a literal substring.
            term = filters.q.strip().replace("\\", "\\\\").replace("%", "\\%")
            term = term.replace("_", "\\_")
            clauses.append(Employee.display_name.ilike(f"%{term}%", escape="\\"))
        if filters.home_unit_id is not None:
            clauses.append(Employee.home_unit_id == filters.home_unit_id)
        if filters.without_home_unit:
            clauses.append(Employee.home_unit_id.is_(None))
        total = self.db.scalar(select(func.count()).select_from(Employee).where(*clauses))
        rows = self.db.scalars(
            select(Employee)
            .options(joinedload(Employee.home_unit))
            .where(*clauses)
            .order_by(Employee.display_name, Employee.id)
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        ).all()
        return rows, total
