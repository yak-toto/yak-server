from collections.abc import Generator

from sqlmodel import Session

from yak_server.database import build_engine


def get_db() -> Generator[Session, None, None]:
    engine = build_engine()

    with Session(engine) as session:
        yield session
