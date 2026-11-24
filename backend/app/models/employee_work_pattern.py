from datetime import datetime, time
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EmployeeWorkPattern(Base):
    __tablename__ = "employee_work_patterns"
    __table_args__ = (
        UniqueConstraint("employee_id", "weekday"),
        CheckConstraint("weekday BETWEEN 0 AND 6", name="weekday_range"),
        CheckConstraint("state IN ('pending', 'working', 'non_working')", name="state_valid"),
        CheckConstraint(
            "state = 'working' OR (start_time IS NULL AND end_time IS NULL "
            "AND break_start_time IS NULL AND break_end_time IS NULL)",
            name="inactive_times_null",
        ),
        CheckConstraint("start_time < end_time", name="shift_order"),
        CheckConstraint("break_start_time < break_end_time", name="break_order"),
        CheckConstraint(
            "(break_start_time >= start_time) AND (break_end_time >= start_time) "
            "AND (break_start_time <= end_time) AND (break_end_time <= end_time)",
            name="break_contained",
        ),
        CheckConstraint(
            "EXTRACT(SECOND FROM start_time) = 0 "
            "AND EXTRACT(SECOND FROM end_time) = 0 "
            "AND EXTRACT(SECOND FROM break_start_time) = 0 "
            "AND EXTRACT(SECOND FROM break_end_time) = 0",
            name="minute_precision",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    weekday: Mapped[int] = mapped_column(SmallInteger)
    state: Mapped[str] = mapped_column(String(16))
    start_time: Mapped[time | None] = mapped_column(Time)
    end_time: Mapped[time | None] = mapped_column(Time)
    break_start_time: Mapped[time | None] = mapped_column(Time)
    break_end_time: Mapped[time | None] = mapped_column(Time)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
