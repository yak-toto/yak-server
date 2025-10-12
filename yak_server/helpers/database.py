from collections.abc import Generator

from sqlalchemy.orm import Session
from yak_server_db import DatabaseConnection

from yak_server.database import (
    build_engine,
    build_local_session_maker,
    compute_database_uri_without_client,
    get_postgres_settings,
)


def get_db() -> Generator[Session, None, None]:
    engine = build_engine()

    local_session_maker = build_local_session_maker(engine)

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
