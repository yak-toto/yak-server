from functools import cache

import pymysql
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


class MySQLSettings(BaseSettings):
    host: str
    user_name: str
    password: str
    port: int
    db: str

    model_config = SettingsConfigDict(
        env_file=".env.mysql",
        env_file_encoding="utf-8",
        env_prefix="mysql_",
    )


@cache
def get_mysql_settings() -> MySQLSettings:
    return MySQLSettings()


def compute_database_uri(
    mysql_client: str,
    mysql_host: str,
    mysql_user_name: str,
    mysql_password: str,
    mysql_port: int,
    mysql_db: str,
) -> str:
    return f"mysql+{mysql_client}://{mysql_user_name}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"


def build_engine() -> Engine:
    mysql_settings = get_mysql_settings()

    database_url = compute_database_uri(
        pymysql.__name__,
        mysql_settings.host,
        mysql_settings.user_name,
        mysql_settings.password,
        mysql_settings.port,
        mysql_settings.db,
    )

    return create_engine(database_url, pool_recycle=7200, pool_pre_ping=True)


def build_local_session_maker() -> Session:
    return sessionmaker(autocommit=False, autoflush=False, bind=build_engine())


Base = declarative_base()
