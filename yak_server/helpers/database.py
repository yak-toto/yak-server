from __future__ import annotations

from typing import TYPE_CHECKING

from yak_server.database import SessionLocal

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.orm import Session


def get_db() -> Generator[Session, None, None]:
    db_connection = SessionLocal()

    try:
        yield db_connection
    finally:
        db_connection.close()
