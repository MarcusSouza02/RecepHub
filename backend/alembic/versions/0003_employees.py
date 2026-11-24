"""Create employee registration without deleting historical links."""

import sqlalchemy as sa

from alembic import op

revision = "0003_employees"
down_revision = "0002_units"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(140), nullable=False),
        sa.Column("home_unit_id", sa.Uuid(), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "display_name = btrim(display_name) AND length(display_name) > 0",
            name=op.f("ck_employees_display_name_nonempty"),
        ),
        sa.ForeignKeyConstraint(
            ["home_unit_id"],
            ["units.id"],
            ondelete="RESTRICT",
            name=op.f("fk_employees_home_unit_id_units"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employees")),
    )
    op.create_index("ix_employees_home_unit_id", "employees", ["home_unit_id"])


def downgrade() -> None:
    op.drop_index("ix_employees_home_unit_id", table_name="employees")
    op.drop_table("employees")
