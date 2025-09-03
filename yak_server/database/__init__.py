from functools import cache

import psycopg
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


class PostgresSettings(BaseSettings):
    host: str
    user: str
    password: str
    port: int
    db: str

    model_config = SettingsConfigDict(
        env_file=".env.db",
        env_file_encoding="utf-8",
        env_prefix="postgres_",
    )


@cache
def get_postgres_settings() -> PostgresSettings:
    return PostgresSettings()


def compute_database_uri(
    client: str,
    host: str,
    user: str,
    password: str,
    port: int,
    db: str,
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
