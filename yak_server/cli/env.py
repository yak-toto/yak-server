import secrets
from enum import Enum
from pathlib import Path
from typing import Any

from yak_server.database import PostgresSettings


class YesOrNo(str, Enum):
    y = "y"
    n = "n"


def write_env_file(env: dict[str, Any], filename: str) -> None:
    Path(filename).write_text(
        "".join([f"{env_var}={env_value}\n" for env_var, env_value in env.items()]),
        encoding="utf-8",
    )


def write_app_env_file(
    debug: bool,  # noqa: FBT001
    jwt_expiration_time: int,
    jwt_refresh_expiration_time: int,
    competition: str,
) -> None:
    env: dict[str, Any] = {}

    env["DEBUG"] = 1 if debug else 0

    env["JWT_EXPIRATION_TIME"] = jwt_expiration_time
    env["JWT_REFRESH_EXPIRATION_TIME"] = jwt_refresh_expiration_time
    env["JWT_SECRET_KEY"] = secrets.token_hex(128)
    env["JWT_REFRESH_SECRET_KEY"] = secrets.token_hex(128)

    # Select competition to load associated rules
    path = Path(__file__).parents[1] / "data"

    env["COMPETITION"] = competition

    data_folder = path / competition
    env["DATA_FOLDER"] = data_folder

    write_env_file(env, ".env")


def write_db_env_file(host: str, user: str, password: str, port: int, db: str) -> None:
    # try to instantiate pydantic model to check if settings are ok
    PostgresSettings(host=host, user=user, password=password, port=port, db=db)

    env_db = {
        "POSTGRES_HOST": host,
        "POSTGRES_USER": user,
        "POSTGRES_PASSWORD": password,
        "POSTGRES_PORT": port,
        "POSTGRES_DB": db,
    }
    write_env_file(env_db, ".env.db")


def init_env(  # noqa: PLR0913, PLR0917
    debug: bool,  # noqa: FBT001
    host: str,
    db_username: str,
    password: str,
    competition: str,
    database: str,
    jwt_expiration: int,
    jwt_refresh_expiration: int,
    port: int,
) -> None:
    write_app_env_file(debug, jwt_expiration, jwt_refresh_expiration, competition)
    write_db_env_file(host, db_username, password, port, database)
