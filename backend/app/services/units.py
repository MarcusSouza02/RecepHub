from app.models.unit import Unit
from app.repositories.units import UnitRepository
from app.schemas.units import UnitOutput
from app.services.auth import AuthError


class UnitService:
    def __init__(self, db):
        self.db = db
        self.repository = UnitRepository(db)

    def get(self, unit_id):
        unit = self.repository.get(unit_id)
        if unit is None:
            raise AuthError(404, "Unidade não encontrada")
        return unit

    def list(self, query):
        items, total = self.repository.list(query)
        return {
            "items": [UnitOutput.model_validate(unit).model_dump() for unit in items],
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
        }

    def create(self, payload):
        unit = Unit(**payload.model_dump())
        self.db.add(unit)
        self.db.commit()
        self.db.refresh(unit)
        return UnitOutput.model_validate(unit).model_dump()

    def patch(self, unit_id, payload):
        unit = self.get(unit_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(unit, key, value)
        self.db.commit()
        self.db.refresh(unit)
        return UnitOutput.model_validate(unit).model_dump()
