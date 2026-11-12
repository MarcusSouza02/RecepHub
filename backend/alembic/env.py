from sqlalchemy.engine import Connection

from alembic import context
from app.core.config import get_settings
from app.database.session import build_engine
from app.models import Base

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def migrate_connection(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Testes podem fornecer conexão explícita, sem ler o .env nem usar o banco da aplicação.
    supplied_connection = context.config.attributes.get("connection")
    if supplied_connection is not None:
        migrate_connection(supplied_connection)
        return

    engine = build_engine(get_settings())
    try:
        with engine.connect() as connection:
            migrate_connection(connection)
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
