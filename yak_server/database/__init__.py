from pydantic import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


class MySQLSettings(BaseSettings):
    user_name: str
    password: str
    db: str
    port: int = 3306

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "mysql_"


def compute_database_uri(
    mysql_user_name: str,
    mysql_password: str,
    mysql_port: int,
    mysql_db: str,
) -> str:
    return f"mysql+pymysql://{mysql_user_name}:{mysql_password}@localhost:{mysql_port}/{mysql_db}"


mysql_settings = MySQLSettings()


SQLALCHEMY_DATABASE_URL = compute_database_uri(
    mysql_settings.user_name,
    mysql_settings.password,
    mysql_settings.port,
    mysql_settings.db,
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
