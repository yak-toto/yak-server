from sqlalchemy.orm import Session

from yak_server.database import SessionLocal


def get_db() -> Session:
    db_connection = SessionLocal()

    try:
        yield db_connection
    finally:
        db_connection.close()
