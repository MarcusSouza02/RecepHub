"""Store seven explicit habitual days for each employee."""

from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision = "0004_employee_work_patterns"
down_revision = "0003_employees"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "employee_work_patterns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("employee_id", sa.Uuid(), nullable=False),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("break_start_time", sa.Time(), nullable=True),
        sa.Column("break_end_time", sa.Time(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_work_patterns")),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            ondelete="CASCADE",
            name=op.f("fk_employee_work_patterns_employee_id_employees"),
        ),
        sa.UniqueConstraint(
            "employee_id", "weekday", name=op.f("uq_employee_work_patterns_employee_id")
        ),
        sa.CheckConstraint(
            "weekday BETWEEN 0 AND 6", name=op.f("ck_employee_work_patterns_weekday_range")
        ),
        sa.CheckConstraint(
            "state IN ('pending', 'working', 'non_working')",
            name=op.f("ck_employee_work_patterns_state_valid"),
        ),
        sa.CheckConstraint(
            "state = 'working' OR (start_time IS NULL AND end_time IS NULL "
            "AND break_start_time IS NULL AND break_end_time IS NULL)",
            name=op.f("ck_employee_work_patterns_inactive_times_null"),
        ),
        sa.CheckConstraint(
            "start_time < end_time", name=op.f("ck_employee_work_patterns_shift_order")
        ),
        sa.CheckConstraint(
            "break_start_time < break_end_time", name=op.f("ck_employee_work_patterns_break_order")
        ),
        sa.CheckConstraint(
            "(break_start_time >= start_time) AND (break_end_time >= start_time) "
            "AND (break_start_time <= end_time) AND (break_end_time <= end_time)",
            name=op.f("ck_employee_work_patterns_break_contained"),
        ),
        sa.CheckConstraint(
            "EXTRACT(SECOND FROM start_time) = 0 "
            "AND EXTRACT(SECOND FROM end_time) = 0 "
            "AND EXTRACT(SECOND FROM break_start_time) = 0 "
            "AND EXTRACT(SECOND FROM break_end_time) = 0",
            name=op.f("ck_employee_work_patterns_minute_precision"),
        ),
    )
    connection = op.get_bind()
    table = sa.table(
        "employee_work_patterns",
        sa.column("id", sa.Uuid()),
        sa.column("employee_id", sa.Uuid()),
        sa.column("weekday", sa.SmallInteger()),
        sa.column("state", sa.String()),
    )
    for employee_id in connection.execute(sa.text("SELECT id FROM employees")).scalars():
        connection.execute(
            table.insert(),
            [
                {"id": uuid4(), "employee_id": employee_id, "weekday": day, "state": "pending"}
                for day in range(7)
            ],
        )


def downgrade():
    op.drop_table("employee_work_patterns")
