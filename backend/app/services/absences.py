from datetime import UTC, datetime

from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy import select

from app.models.absence import Absence, AbsenceEvent
from app.models.employee import Employee
from app.repositories.absences import AbsenceRepository
from app.schemas.absences import AbsenceFields
from app.services.auth import AuthError

FIELDS = (
    "id",
    "employee_id",
    "type",
    "mode",
    "start_date",
    "end_date",
    "start_time",
    "end_time",
    "notes",
    "status",
    "version",
    "created_at",
    "updated_at",
    "cancelled_at",
)


def periods_overlap(left, right):
    if left.end_date < right.start_date or right.end_date < left.start_date:
        return False
    if left.mode == "full_day" or right.mode == "full_day":
        return True
    return left.start_time < right.end_time and right.start_time < left.end_time


class AbsenceService:
    def __init__(self, db):
        self.db = db
        self.repository = AbsenceRepository(db)

    def employee(self, employee_id, *, lock=False):
        query = select(Employee).where(Employee.id == employee_id)
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        employee = self.db.scalar(query)
        if employee is None:
            raise AuthError(404, "Colaboradora não encontrada")
        return employee

    def get(self, absence_id, *, lock=False):
        row = self.repository.get(absence_id)
        if row is None:
            raise AuthError(404, "Ausência não encontrada")
        if lock:
            self.employee(row.employee_id, lock=True)
            row = self.repository.get(absence_id, lock=True)
            if row is None:
                raise AuthError(404, "Ausência não encontrada")
        return row

    def representation(self, row):
        overlaps = (
            []
            if row.status != "active"
            else [
                candidate.id
                for candidate in self.repository.overlap_candidates(row)
                if periods_overlap(row, candidate)
            ]
        )
        return {
            **{key: getattr(row, key) for key in FIELDS},
            "employee_name": self.employee(row.employee_id).display_name,
            "overlap_warning": bool(overlaps),
            "overlap_ids": overlaps,
        }

    def detail(self, absence_id):
        return self.representation(self.get(absence_id))

    def list(self, filters):
        rows, total = self.repository.list(filters)
        return {
            "items": [self.representation(row) for row in rows],
            "total": total,
            "page": filters.page,
            "page_size": filters.page_size,
        }

    def event(self, row, action):
        self.db.flush()
        self.db.refresh(row)
        self.db.add(
            AbsenceEvent(
                absence_id=row.id,
                version=row.version,
                action=action,
                snapshot=jsonable_encoder(self.representation(row)),
            )
        )

    def create(self, payload):
        self.employee(payload.employee_id, lock=True)
        row = Absence(**payload.model_dump())
        self.db.add(row)
        self.event(row, "created")
        self.db.commit()
        return self.representation(row)

    @staticmethod
    def check_version(row, version):
        if row.version != version:
            raise AuthError(409, "A ausência foi alterada; atualize os dados")

    def patch(self, absence_id, payload):
        row = self.get(absence_id, lock=True)
        self.check_version(row, payload.expected_version)
        if row.status != "active":
            raise AuthError(409, "Ausência cancelada não pode ser alterada")
        changes = payload.model_dump(exclude_unset=True, exclude={"expected_version"})
        merged = {key: getattr(row, key) for key in AbsenceFields.model_fields}
        merged.update(changes)
        try:
            validated = AbsenceFields.model_validate(merged)
        except ValidationError:
            raise AuthError(422, "Dados da ausência inválidos") from None
        for key, value in validated.model_dump().items():
            setattr(row, key, value)
        row.version += 1
        row.updated_at = datetime.now(UTC)
        self.event(row, "updated")
        self.db.commit()
        return self.representation(row)

    def cancel(self, absence_id, payload):
        row = self.get(absence_id, lock=True)
        if row.status == "cancelled":
            return self.representation(row)
        self.check_version(row, payload.expected_version)
        row.status = "cancelled"
        row.cancelled_at = row.updated_at = datetime.now(UTC)
        row.version += 1
        self.event(row, "cancelled")
        self.db.commit()
        return self.representation(row)

    def events(self, absence_id):
        self.get(absence_id)
        return {
            "items": [
                {
                    "id": event.id,
                    "absence_id": event.absence_id,
                    "version": event.version,
                    "action": event.action,
                    "snapshot": event.snapshot,
                    "created_at": event.created_at,
                }
                for event in self.repository.events(absence_id)
            ]
        }
