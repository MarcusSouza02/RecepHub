from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Unit(Base):
    __tablename__ = "units"
    __table_args__ = (
        CheckConstraint("length(name) BETWEEN 1 AND 120 AND name = btrim(name)", name="name_valid"),
        CheckConstraint(
            "city IS NULL OR (length(city) BETWEEN 1 AND 120 AND city = btrim(city))",
            name="city_valid",
        ),
        CheckConstraint(
            "description IS NULL OR (length(description) BETWEEN 1 AND 500 "
            "AND description = btrim(description))",
            name="description_valid",
        ),
        CheckConstraint("updated_at >= created_at", name="timestamps_consistent"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120))
    city: Mapped[str | None] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
