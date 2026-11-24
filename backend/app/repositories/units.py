from sqlalchemy import func, or_, select

from app.models.unit import Unit


class UnitRepository:
    def __init__(self, db):
        self.db = db

    def get(self, unit_id):
        return self.db.get(Unit, unit_id)

    def list(self, query):
        filters = []
        if query.status != "all":
            filters.append(Unit.active.is_(query.status == "active"))
        if query.q:
            literal = query.q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{literal}%"
            filters.append(
                or_(Unit.name.ilike(pattern, escape="\\"), Unit.city.ilike(pattern, escape="\\"))
            )
        total = self.db.scalar(select(func.count()).select_from(Unit).where(*filters))
        items = self.db.scalars(
            select(Unit)
            .where(*filters)
            .order_by(Unit.name, Unit.id)
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        ).all()
        return items, total
