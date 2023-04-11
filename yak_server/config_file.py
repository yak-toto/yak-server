import json
import os
import sys
from configparser import ConfigParser

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources

from pathlib import Path

from .helpers.rules import RULE_MAPPING


class RuleNotDefined(Exception):
    def __init__(self, rule_id) -> None:
        super().__init__(f"Rule not defined: {rule_id}")


def compute_database_uri(mysql_user_name, mysql_password, mysql_port, mysql_db) -> str:
    return f"mysql+pymysql://{mysql_user_name}:{mysql_password}@localhost:{mysql_port}/{mysql_db}"


def get_mysql_config() -> dict:
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


def get_jwt_config() -> dict:
    return {
        "SECRET_KEY": os.environ["JWT_SECRET_KEY"],
        "JWT_EXPIRATION_TIME": int(os.environ["JWT_EXPIRATION_TIME"]),
    }


def get_yak_config() -> dict:
    with resources.as_file(
        resources.files("yak_server") / "data" / os.environ["COMPETITION"],
    ) as path:
        data_folder = path

    config = ConfigParser()
    config.read(f"{data_folder}/config.ini")

    rules = {}

    for rule_file in Path(f"{data_folder}/rules").glob("*.json"):
        rule_id = rule_file.stem

        if rule_id not in RULE_MAPPING:
            raise RuleNotDefined(rule_id)

        with rule_file.open() as rule_content:
            rules[rule_id] = json.loads(rule_content.read())

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
        "DATA_FOLDER": data_folder,
        "RULES": rules,
    }


def get_config() -> dict:
    return {**get_mysql_config(), **get_jwt_config(), **get_yak_config()}
