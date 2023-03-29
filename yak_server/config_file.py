import json
import os
import sys
from configparser import ConfigParser

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources

from pathlib import Path


def compute_database_uri(mysql_user_name, mysql_password, mysql_port, mysql_db):
    return f"mysql+pymysql://{mysql_user_name}:{mysql_password}@localhost:{mysql_port}/{mysql_db}"


def get_mysql_config():
    mysql_config = {
        "MYSQL_USER_NAME": os.environ["MYSQL_USER_NAME"],
        "MYSQL_PASSWORD": os.environ["MYSQL_PASSWORD"],
        "MYSQL_PORT": os.environ.get("MYSQL_PORT", 3306),
        "MYSQL_DB": os.environ["MYSQL_DB"],
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    }

    mysql_config["SQLALCHEMY_DATABASE_URI"] = compute_database_uri(
        mysql_config["MYSQL_USER_NAME"],
        mysql_config["MYSQL_PASSWORD"],
        mysql_config["MYSQL_PORT"],
        mysql_config["MYSQL_DB"],
    )

    return mysql_config


def get_jwt_config():
    return {
        "SECRET_KEY": os.environ["JWT_SECRET_KEY"],
        "JWT_EXPIRATION_TIME": int(os.environ["JWT_EXPIRATION_TIME"]),
    }


def get_yak_config():
    with resources.as_file(
        resources.files("yak_server") / "data" / os.environ["COMPETITION"],
    ) as path:
        DATA_FOLDER = path

    config = ConfigParser()
    config.read(f"{DATA_FOLDER}/config.ini")

    with Path(f"{DATA_FOLDER}/finale_phase_config.json").open() as file:
        FINALE_PHASE_CONFIG = json.loads(file.read())

    with resources.as_file(
        resources.files("yak_server") / "data" / os.environ["COMPETITION"],
    ) as path:
        DATA_FOLDER = path

    config = ConfigParser()
    config.read(f"{DATA_FOLDER}/config.ini")

    with Path(f"{DATA_FOLDER}/finale_phase_config.json").open() as file:
        FINALE_PHASE_CONFIG = json.loads(file.read())

    return {
        # SQL Alchemy features
        "LOCK_DATETIME": config.get("locking", "datetime"),
        "BASE_CORRECT_RESULT": config.getint("points", "base_correct_result"),
        "MULTIPLYING_FACTOR_CORRECT_RESULT": config.getint(
            "points",
            "multiplying_factor_correct_result",
        ),
        "BASE_CORRECT_SCORE": config.getint("points", "base_correct_score"),
        "MULTIPLYING_FACTOR_CORRECT_SCORE": config.getint(
            "points",
            "multiplying_factor_correct_score",
        ),
        "TEAM_QUALIFIED": config.getint("points", "team_qualified"),
        "FIRST_TEAM_QUALIFIED": config.getint("points", "first_team_qualified"),
        "FINALE_PHASE_CONFIG": FINALE_PHASE_CONFIG,
        "DATA_FOLDER": DATA_FOLDER,
    }


def get_config():
    return {**get_mysql_config(), **get_jwt_config(), **get_yak_config()}
