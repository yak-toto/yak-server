from collections.abc import Generator
from functools import cache

from sqlalchemy.orm import Session, sessionmaker
from yak_server_db import DatabaseConnection

from yak_server.database import (
    build_engine,
    build_local_session_maker,
    compute_database_uri_without_client,
    get_postgres_settings,
)


# Cache SQLAlchemy engine and session maker (singleton pattern)
@cache
def _get_sqlalchemy_session_maker() -> sessionmaker[Session]:
    engine = build_engine()
    return build_local_session_maker(engine)


def get_db() -> Generator[Session, None, None]:
    """Get SQLAlchemy database session with cached engine."""
    local_session_maker = _get_sqlalchemy_session_maker()

    with local_session_maker() as db:
        yield db


# Global singleton for database connection
_db_connection: DatabaseConnection | None = None


async def get_db_rust() -> DatabaseConnection:
    """Get a cached database connection (singleton pattern for async).

    Returns:
        DatabaseConnection: A shared database connection instance.
    """
    global _db_connection

    if _db_connection is None:
        postgres_settings = get_postgres_settings()

        database_url = compute_database_uri_without_client(
            postgres_settings.host,
            postgres_settings.user,
            postgres_settings.password,
            postgres_settings.port,
            postgres_settings.db,
        )

        _db_connection = await DatabaseConnection.connect(database_url)

    return _db_connection
