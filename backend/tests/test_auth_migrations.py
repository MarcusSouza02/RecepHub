from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

from alembic import command
from app.models import User, UserSession
from tests.database import migration_config

pytestmark = pytest.mark.integration


def test_upgrade_downgrade_upgrade_with_data(migrated_database):
    with migrated_database.begin() as connection:
        config = migration_config(connection)
        command.upgrade(config, "head")
        assert set(inspect(connection).get_table_names()) == {
            "alembic_version",
            "users",
            "user_sessions",
        }
        assert (
            MigrationContext.configure(connection).get_current_revision() == "0001_auth_foundation"
        )
        command.check(config)

        # Dados exclusivamente fictícios, para exercitar a remoção na ordem das FKs.
        account_id = uuid4()
        created_at = datetime(2026, 1, 1, tzinfo=UTC)
        connection.execute(
            User.__table__.insert().values(
                id=account_id,
                username="migracao.demo",
                password_hash="fixture-only-not-a-real-hash",
            )
        )
        connection.execute(
            UserSession.__table__.insert().values(
                user_id=account_id,
                token_hash="a" * 64,
                created_at=created_at,
                last_seen_at=created_at,
                expires_at=created_at + timedelta(hours=12),
            )
        )
        command.downgrade(config, "base")
        assert set(inspect(connection).get_table_names()) == {"alembic_version"}
        assert MigrationContext.configure(connection).get_current_revision() is None

        command.upgrade(config, "head")
        command.check(config)
        assert (
            MigrationContext.configure(connection).get_current_revision() == "0001_auth_foundation"
        )
        for table in ("users", "user_sessions"):
            assert connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0
