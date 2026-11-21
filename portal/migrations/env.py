"""Use a direct Neon endpoint for migrations, not a transaction pooler."""
from alembic import context
from sqlalchemy import create_engine, pool

from portal.db import Base, migration_url
import portal.models  # noqa: F401

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=migration_url(), target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = create_engine(migration_url(), poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
