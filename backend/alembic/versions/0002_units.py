"""Create units without seeds or name uniqueness."""

import sqlalchemy as sa

from alembic import op

revision = "0002_units"
down_revision = "0001_auth_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "units",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("city", sa.String(120), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "length(name) BETWEEN 1 AND 120 AND name = btrim(name)",
            name=op.f("ck_units_name_valid"),
        ),
        sa.CheckConstraint(
            "city IS NULL OR (length(city) BETWEEN 1 AND 120 AND city = btrim(city))",
            name=op.f("ck_units_city_valid"),
        ),
        sa.CheckConstraint(
            "description IS NULL OR (length(description) BETWEEN 1 AND 500 "
            "AND description = btrim(description))",
            name=op.f("ck_units_description_valid"),
        ),
        sa.CheckConstraint("updated_at >= created_at", name=op.f("ck_units_timestamps_consistent")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_units")),
    )


def downgrade() -> None:
    op.drop_table("units")
