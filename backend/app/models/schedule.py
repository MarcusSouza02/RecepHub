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


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = (
        CheckConstraint("EXTRACT(ISODOW FROM week_start) = 1", name="week_monday"),
        CheckConstraint("status IN ('draft', 'published')", name="status_valid"),
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint("latest_revision_number >= 0", name="revision_nonnegative"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    week_start: Mapped[date] = mapped_column(Date, unique=True)
    status: Mapped[str] = mapped_column(String(16), default="draft", server_default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    latest_revision_number: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ScheduleEmployeeDay(Base):
    __tablename__ = "schedule_employee_days"
    __table_args__ = (
        UniqueConstraint("schedule_id", "employee_id", "work_date"),
        CheckConstraint(
            "state IN ('pending', 'working', 'non_working', 'excluded')", name="state_valid"
        ),
        CheckConstraint(
            "state <> 'excluded' OR (resolution_note IS NOT NULL "
            "AND length(btrim(resolution_note)) > 0)",
            name="exclusion_reason",
        ),
        CheckConstraint("length(btrim(employee_name_snapshot)) > 0", name="name_nonempty"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    schedule_id: Mapped[UUID] = mapped_column(
        ForeignKey("schedules.id", ondelete="CASCADE"), index=True
    )
    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), index=True
    )
    work_date: Mapped[date] = mapped_column(Date)
    state: Mapped[str] = mapped_column(String(16))
    employee_name_snapshot: Mapped[str] = mapped_column(String(140))
    source_data: Mapped[dict] = mapped_column(JSONB)
    resolution_note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ScheduleAssignment(Base):
    __tablename__ = "schedule_assignments"
    __table_args__ = (
        CheckConstraint("start_time < end_time", name="shift_order"),
        CheckConstraint(
            "(break_start_time IS NULL) = (break_end_time IS NULL)", name="break_complete"
        ),
        CheckConstraint("break_start_time < break_end_time", name="break_order"),
        CheckConstraint(
            "break_start_time >= start_time AND break_end_time <= end_time", name="break_contained"
        ),
        CheckConstraint(
            "EXTRACT(SECOND FROM start_time) = 0 AND EXTRACT(SECOND FROM end_time) = 0 "
            "AND EXTRACT(SECOND FROM break_start_time) = 0 "
            "AND EXTRACT(SECOND FROM break_end_time) = 0",
            name="minute_precision",
        ),
        CheckConstraint("length(btrim(unit_name_snapshot)) > 0", name="unit_name_nonempty"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    day_id: Mapped[UUID] = mapped_column(
        ForeignKey("schedule_employee_days.id", ondelete="CASCADE"), index=True
    )
    unit_id: Mapped[UUID] = mapped_column(ForeignKey("units.id", ondelete="RESTRICT"), index=True)
    unit_name_snapshot: Mapped[str] = mapped_column(String(120))
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    break_start_time: Mapped[time | None] = mapped_column(Time)
    break_end_time: Mapped[time | None] = mapped_column(Time)
    position: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ScheduleRevision(Base):
    __tablename__ = "schedule_revisions"
    __table_args__ = (
        UniqueConstraint("schedule_id", "number"),
        CheckConstraint("number >= 1", name="number_positive"),
        CheckConstraint("source_version >= 1", name="source_version_positive"),
        CheckConstraint("schema_version >= 1", name="schema_version_positive"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    schedule_id: Mapped[UUID] = mapped_column(
        ForeignKey("schedules.id", ondelete="RESTRICT"), index=True
    )
    number: Mapped[int] = mapped_column(Integer)
    source_version: Mapped[int] = mapped_column(Integer)
    schema_version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    snapshot: Mapped[dict] = mapped_column(JSONB)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
