import logging
from logging.config import fileConfig

from alembic import context

from yak_server.database import engine
from yak_server.database.models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")


def get_engine_url():
    try:
        return engine.url.render_as_string(hide_password=False).replace("%", "%%")
    except AttributeError:
        return str(engine.url).replace("%", "%%")


# add your model's MetaData object here
# for 'autogenerate' support
config.set_main_option("sqlalchemy.url", get_engine_url())

# other values from the config, defined by the needs of env.py,
# can be acquired:
# ... etc.


def get_metadata():
    if hasattr(Base, "metadatas"):
        return Base.metadatas[None]
    return Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=get_metadata(), literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
