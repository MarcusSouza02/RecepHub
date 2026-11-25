from datetime import date, datetime, time
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Absence(Base):
    __tablename__ = "absences"
    __table_args__ = (
        CheckConstraint("type IN ('vacation','day_off','compensation','other')", name="type_valid"),
        CheckConstraint("mode IN ('full_day','partial')", name="mode_valid"),
        CheckConstraint("start_date <= end_date", name="dates_ordered"),
        CheckConstraint(
            "(mode = 'full_day' AND start_time IS NULL AND end_time IS NULL) OR "
            "(mode = 'partial' AND start_date = end_date AND start_time IS NOT NULL "
            "AND end_time IS NOT NULL AND start_time < end_time)",
            name="period_valid",
        ),
        CheckConstraint(
            "EXTRACT(SECOND FROM start_time) = 0 AND EXTRACT(SECOND FROM end_time) = 0",
            name="minute_precision",
        ),
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint(
            "(status = 'active' AND cancelled_at IS NULL) OR "
            "(status = 'cancelled' AND cancelled_at IS NOT NULL)",
            name="status_valid",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), index=True
    )
    type: Mapped[str] = mapped_column(String(16))
    mode: Mapped[str] = mapped_column(String(16))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time | None] = mapped_column(Time)
    end_time: Mapped[time | None] = mapped_column(Time)
    notes: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(16), default="active", server_default="active")
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AbsenceEvent(Base):
    __tablename__ = "absence_events"
    __table_args__ = (
        UniqueConstraint("absence_id", "version"),
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint("action IN ('created','updated','cancelled')", name="action_valid"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    absence_id: Mapped[UUID] = mapped_column(
        ForeignKey("absences.id", ondelete="RESTRICT"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(16))
    snapshot: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
