"""Create the single administrative account and its sessions.

Revision ID: 0001_auth_foundation
Revises: None
"""

import sqlalchemy as sa

from alembic import op

revision = "0001_auth_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(80), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("login_window_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "login_attempt_count", sa.SmallInteger(), server_default=sa.text("0"), nullable=False
        ),
        sa.CheckConstraint(
            "username COLLATE \"C\" ~ '^[a-z0-9._-]{3,80}$'",
            name=op.f("ck_users_username_canonical"),
        ),
        sa.CheckConstraint(
            "login_attempt_count BETWEEN 0 AND 5", name=op.f("ck_users_login_attempt_count_range")
        ),
        sa.CheckConstraint(
            "login_window_started_at IS NOT NULL OR login_attempt_count = 0",
            name=op.f("ck_users_login_window_consistent"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
    )
    op.create_index("uq_users_single_account", "users", [sa.text("(true)")], unique=True)
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.CHAR(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "token_hash COLLATE \"C\" ~ '^[0-9a-f]{64}$'",
            name=op.f("ck_user_sessions_token_hash_format"),
        ),
        sa.CheckConstraint(
            "expires_at > created_at", name=op.f("ck_user_sessions_expires_after_creation")
        ),
        sa.CheckConstraint(
            "last_seen_at >= created_at AND last_seen_at < expires_at",
            name=op.f("ck_user_sessions_last_seen_in_lifetime"),
        ),
        sa.CheckConstraint(
            "revoked_at IS NULL OR revoked_at >= created_at",
            name=op.f("ck_user_sessions_revoked_after_creation"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_user_sessions_token_hash")),
    )
    op.create_index(op.f("ix_user_sessions_user_id"), "user_sessions", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_user_sessions_user_id"), table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index("uq_users_single_account", table_name="users")
    op.drop_table("users")
