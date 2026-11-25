from sqlalchemy import func, select

from app.models.absence import Absence, AbsenceEvent


class AbsenceRepository:
    def __init__(self, db):
        self.db = db

    def get(self, absence_id, *, lock=False):
        query = select(Absence).where(Absence.id == absence_id)
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        return self.db.scalar(query)

    def list(self, filters):
        clauses = []
        for key in ("employee_id", "type"):
            if getattr(filters, key) is not None:
                clauses.append(getattr(Absence, key) == getattr(filters, key))
        if filters.status != "all":
            clauses.append(Absence.status == filters.status)
        if filters.from_date:
            clauses.append(Absence.end_date >= filters.from_date)
        if filters.to_date:
            clauses.append(Absence.start_date <= filters.to_date)
        total = self.db.scalar(select(func.count()).select_from(Absence).where(*clauses))
        rows = self.db.scalars(
            select(Absence)
            .where(*clauses)
            .order_by(Absence.start_date.desc(), Absence.id)
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        ).all()
        return rows, total

    def overlap_candidates(self, absence):
        return self.db.scalars(
            select(Absence)
            .where(
                Absence.employee_id == absence.employee_id,
                Absence.id != absence.id,
                Absence.status == "active",
                Absence.start_date <= absence.end_date,
                Absence.end_date >= absence.start_date,
            )
            .order_by(Absence.start_date, Absence.id)
        ).all()

    def events(self, absence_id):
        return self.db.scalars(
            select(AbsenceEvent)
            .where(AbsenceEvent.absence_id == absence_id)
            .order_by(AbsenceEvent.version)
        ).all()
