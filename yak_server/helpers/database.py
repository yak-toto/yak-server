from collections.abc import Generator

from sqlmodel import Session

from yak_server.database import build_engine


def get_db() -> Generator[Session, None, None]:
    with Session(build_engine()) as session:
        try:
            yield session
        finally:
            session.close()
