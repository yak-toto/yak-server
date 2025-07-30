from collections.abc import Generator

from sqlalchemy.orm import Session

from yak_server.database import build_engine, build_local_session_maker


def get_db() -> Generator[Session, None, None]:
    engine = build_engine()

    local_session_maker = build_local_session_maker(engine)

    with local_session_maker() as db:
        yield db
