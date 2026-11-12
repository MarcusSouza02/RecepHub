from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user_session import UserSession


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "username COLLATE \"C\" ~ '^[a-z0-9._-]{3,80}$'", name="username_canonical"
        ),
        CheckConstraint("login_attempt_count BETWEEN 0 AND 5", name="login_attempt_count_range"),
        CheckConstraint(
            "login_window_started_at IS NOT NULL OR login_attempt_count = 0",
            name="login_window_consistent",
        ),
        Index("uq_users_single_account", text("(true)"), unique=True),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    login_window_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    login_attempt_count: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))

    sessions: Mapped[list[UserSession]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
