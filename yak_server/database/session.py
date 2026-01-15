import psycopg
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from .settings import get_postgres_settings


def compute_database_uri(
    client: str, host: str, user: str, password: str, port: int, db: str
) -> str:
    return f"postgresql+{client}://{user}:{password}@{host}:{port}/{db}"


def build_engine() -> Engine:
    postgres_settings = get_postgres_settings()

    database_url = compute_database_uri(
        psycopg.__name__,
        postgres_settings.host,
        postgres_settings.user,
        postgres_settings.password,
        postgres_settings.port,
        postgres_settings.db,
    )

    return create_engine(database_url, pool_recycle=7200, pool_pre_ping=True)


def build_local_session_maker(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
