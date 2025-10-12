from collections.abc import Generator
from functools import cache

from sqlalchemy.orm import Session, sessionmaker

from yak_server.database import build_engine, build_local_session_maker


@cache
def _get_sqlalchemy_session_maker() -> sessionmaker[Session]:
    engine = build_engine()
    return build_local_session_maker(engine)


def get_db() -> Generator[Session, None, None]:
    local_session_maker = _get_sqlalchemy_session_maker()

    with local_session_maker() as db:
        yield db
