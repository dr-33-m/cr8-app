from logging.config import fileConfig
from sqlmodel import SQLModel
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.models import User, Project, Asset, Template, Moodboard  # Import all models
from app.core.config import settings  # Your settings file

# This is the Alembic Config object, which provides access to the values within the .ini file.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# Add your metadata here for 'autogenerate' support
# target_metadata is used by Alembic to detect changes
target_metadata = SQLModel.metadata

# Get the database URL dynamically from your settings
config.set_main_option("sqlalchemy.url", settings.postgres_url)

# Run migrations


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection,
                          target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
