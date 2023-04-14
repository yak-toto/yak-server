import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv(".flaskenv")


def compute_database_uri(mysql_user_name, mysql_password, mysql_port, mysql_db) -> str:
    return f"mysql+pymysql://{mysql_user_name}:{mysql_password}@localhost:{mysql_port}/{mysql_db}"


SQLALCHEMY_DATABASE_URL = compute_database_uri(
    os.environ["MYSQL_USER_NAME"],
    os.environ["MYSQL_PASSWORD"],
    os.environ.get("MYSQL_PORT", 3306),
    os.environ["MYSQL_DB"],
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
