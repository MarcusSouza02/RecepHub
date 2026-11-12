"""Explicitly targeted PostgreSQL test connections and programmatic Alembic configuration."""

from pathlib import Path

from alembic.config import Config
from sqlalchemy.engine import URL, Connection, make_url
from sqlalchemy.exc import ArgumentError


def validate_test_database_url(value: str) -> URL:
    try:
        url = make_url(value)
    except (ArgumentError, ValueError):
        raise ValueError(
            "TEST_DATABASE_URL inválida; não use a URL do banco de desenvolvimento"
        ) from None
    if (
        url.drivername != "postgresql+psycopg"
        or not url.database
        or not url.database.endswith("_test")
        or url.query
    ):
        raise ValueError("Use PostgreSQL+psycopg, banco terminado em _test e URL sem parâmetros")
    return url


def require_test_database_reset(value: str | None) -> None:
    if value != "1":
        raise ValueError(
            "Migrações de teste exigem TEST_DATABASE_ALLOW_RESET=1 em banco descartável"
        )


def migration_config(connection: Connection) -> Config:
    backend = Path(__file__).resolve().parents[1]
    config = Config(str(backend / "alembic.ini"))
    config.set_main_option("script_location", str(backend / "alembic"))
    config.attributes["connection"] = connection
    return config
