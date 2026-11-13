import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from alembic import command
from app.core.config import Settings
from app.main import create_app
from app.models import Base
from tests.database import migration_config, require_test_database_reset, validate_test_database_url


@pytest.fixture
def client():
    app = create_app(Settings(_env_file=None))
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def postgres_engine():
    value = os.getenv("TEST_DATABASE_URL")
    if not value:
        pytest.skip("Defina TEST_DATABASE_URL apontando para PostgreSQL descartável")
    url = validate_test_database_url(value)
    engine = create_engine(
        url,
        poolclass=NullPool,
        connect_args={"connect_timeout": 3, "options": "-c statement_timeout=3000"},
    )
    try:
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT current_database()")).scalar_one() == url.database
            )
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def migrated_database(postgres_engine):
    require_test_database_reset(os.getenv("TEST_DATABASE_ALLOW_RESET"))
    with postgres_engine.begin() as connection:
        existing = set(inspect(connection).get_table_names(schema="public"))
        expected = set(Base.metadata.tables) | {"alembic_version"}
        if existing - expected:
            pytest.fail("Banco de teste contém tabelas inesperadas; nenhuma migração foi executada")
        # Recusar banco populado, mesmo com nome de teste: nunca apagar registros preexistentes.
        for table in Base.metadata.tables:
            if (
                table in existing
                and connection.execute(text(f"SELECT count(*) FROM {table}")).scalar()
            ):
                pytest.fail(
                    "Banco de teste contém dados preexistentes; use um banco descartável vazio"
                )
        command.upgrade(migration_config(connection), "head")
    return postgres_engine


@pytest.fixture
def db_session(migrated_database):
    with migrated_database.connect() as connection:
        transaction = connection.begin()
        try:
            # Até commits internos do código sob teste ficam contidos no rollback externo.
            with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                yield session
        finally:
            transaction.rollback()
