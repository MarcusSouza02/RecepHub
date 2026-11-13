from sqlalchemy import select

from app.models.employee import Employee
from app.models.unit import Unit
from app.repositories.employees import EmployeeRepository
from app.services.auth import AuthError


def representation(employee):
    unit = employee.home_unit
    return {
        "id": employee.id,
        "display_name": employee.display_name,
        "home_unit_id": employee.home_unit_id,
        "home_unit_name": unit.name if unit else None,
        "home_unit_active": unit.active if unit else None,
        "notes": employee.notes,
        "active": employee.active,
        "created_at": employee.created_at,
        "updated_at": employee.updated_at,
    }


class EmployeeService:
    def __init__(self, db):
        self.db = db
        self.repository = EmployeeRepository(db)

    def require_unit(self, unit_id, *, active=False):
        # Shared with unit updates: serialize a new link against unit inactivation.
        unit = self.db.scalar(select(Unit).where(Unit.id == unit_id).with_for_update())
        if unit is None:
            raise AuthError(404, "Unidade não encontrada")
        if active and not unit.active:
            raise AuthError(409, "Novos vínculos exigem uma unidade ativa")
        return unit

    def get(self, employee_id, *, lock=False):
        employee = self.repository.get(employee_id, lock=lock)
        if employee is None:
            raise AuthError(404, "Colaboradora não encontrada")
        return employee

    def list(self, filters):
        rows, total = self.repository.list(filters)
        return {
            "items": [representation(row) for row in rows],
            "total": total,
            "page": filters.page,
            "page_size": filters.page_size,
        }

    def create(self, payload):
        values = payload.model_dump()
        if payload.home_unit_id is not None:
            self.require_unit(payload.home_unit_id, active=True)
        employee = Employee(**values)
        self.db.add(employee)
        self.db.flush()
        self.db.commit()
        return representation(self.get(employee.id))

    def patch(self, employee_id, payload):
        employee = self.get(employee_id, lock=True)
        values = payload.model_dump(exclude_unset=True)
        unit_id = values.get("home_unit_id")
        if unit_id is not None and unit_id != employee.home_unit_id:
            self.require_unit(unit_id, active=True)
        for name, value in values.items():
            setattr(employee, name, value)
        self.db.commit()
        self.db.refresh(employee)
        return representation(employee)
