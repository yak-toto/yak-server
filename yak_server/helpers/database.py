from collections.abc import Generator

from sqlalchemy.orm import Session

from yak_server.database import build_local_session_maker


def get_db() -> Generator[Session, None, None]:
    local_session_maker = build_local_session_maker()

    with local_session_maker() as db:
        try:
            yield db
        finally:
            db.close()
