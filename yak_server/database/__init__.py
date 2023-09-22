from functools import lru_cache

import pymysql
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


class MySQLSettings(BaseSettings):
    user_name: str = ""
    password: str = ""
    port: int = 3306
    db: str = ""

    model_config = SettingsConfigDict(
        env_file=".env.mysql",
        env_file_encoding="utf-8",
        env_prefix="mysql_",
    )


@lru_cache(maxsize=None)
def get_mysql_settings() -> MySQLSettings:
    return MySQLSettings()


def compute_database_uri(
    mysql_client: str,
    mysql_user_name: str,
    mysql_password: str,
    mysql_port: int,
    mysql_db: str,
) -> str:
    return f"mysql+{mysql_client}://{mysql_user_name}:{mysql_password}@127.0.0.1:{mysql_port}/{mysql_db}"


mysql_settings = get_mysql_settings()


SQLALCHEMY_DATABASE_URL = compute_database_uri(
    pymysql.__name__,
    mysql_settings.user_name,
    mysql_settings.password,
    mysql_settings.port,
    mysql_settings.db,
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_recycle=7200, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
