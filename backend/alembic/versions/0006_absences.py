"""Persist operational absences and their event history."""

from alembic import op

revision = "0006_absences"
down_revision = "0005_schedules"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""

CREATE TABLE absences (
        id UUID NOT NULL,
        employee_id UUID NOT NULL,
        type VARCHAR(16) NOT NULL,
        mode VARCHAR(16) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        start_time TIME WITHOUT TIME ZONE,
        end_time TIME WITHOUT TIME ZONE,
        notes VARCHAR(500),
        status VARCHAR(16) DEFAULT 'active' NOT NULL,
        version INTEGER DEFAULT '1' NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
        cancelled_at TIMESTAMP WITH TIME ZONE,
        CONSTRAINT pk_absences PRIMARY KEY (id),
        CONSTRAINT ck_absences_type_valid CHECK (type IN
('vacation','day_off','compensation','other')),
        CONSTRAINT ck_absences_mode_valid CHECK (mode IN ('full_day','partial')),
        CONSTRAINT ck_absences_dates_ordered CHECK (start_date <= end_date),
        CONSTRAINT ck_absences_period_valid CHECK ((mode = 'full_day' AND start_time IS
NULL AND end_time IS NULL) OR (mode = 'partial' AND start_date = end_date AND start_time
IS NOT NULL AND end_time IS NOT NULL AND start_time < end_time)),
        CONSTRAINT ck_absences_minute_precision CHECK (EXTRACT(SECOND FROM start_time) =
0 AND EXTRACT(SECOND FROM end_time) = 0),
        CONSTRAINT ck_absences_version_positive CHECK (version >= 1),
        CONSTRAINT ck_absences_status_valid CHECK ((status = 'active' AND cancelled_at
IS NULL) OR (status = 'cancelled' AND cancelled_at IS NOT NULL)),
        CONSTRAINT fk_absences_employee_id_employees FOREIGN KEY(employee_id) REFERENCES
employees (id) ON DELETE RESTRICT
)

    """)
    op.execute("CREATE INDEX ix_absences_employee_id ON absences (employee_id)")
    op.execute("""

CREATE TABLE absence_events (
        id UUID NOT NULL,
        absence_id UUID NOT NULL,
        version INTEGER NOT NULL,
        action VARCHAR(16) NOT NULL,
        snapshot JSONB NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
        CONSTRAINT pk_absence_events PRIMARY KEY (id),
        CONSTRAINT uq_absence_events_absence_id UNIQUE (absence_id, version),
        CONSTRAINT ck_absence_events_version_positive CHECK (version >= 1),
        CONSTRAINT ck_absence_events_action_valid CHECK (action IN
('created','updated','cancelled')),
        CONSTRAINT fk_absence_events_absence_id_absences FOREIGN KEY(absence_id)
REFERENCES absences (id) ON DELETE RESTRICT
)

    """)
    op.execute("CREATE INDEX ix_absence_events_absence_id ON absence_events (absence_id)")


def downgrade():
    op.drop_table("absence_events")
    op.drop_table("absences")
