import json
import os
from pathlib import Path

import pkg_resources


def load_business_rules(competition):
    from configparser import ConfigParser

    filename = pkg_resources.resource_filename(__name__, f"data/{competition}/config.ini")

    config = ConfigParser()
    config.read(filename)
    return config


COMPETITION = os.environ["COMPETITION"]

config = load_business_rules(COMPETITION)

with Path(
    pkg_resources.resource_filename(__name__, f"data/{COMPETITION}/finale_phase_config.json"),
).open() as file:
    FINALE_PHASE_CONFIG = json.loads(file.read())

YAK_CONFIG = {
    # Setup MySQL credentials
    "SQLALCHEMY_DATABASE_URI": (
        f"mysql+pymysql://{os.environ['MYSQL_USER_NAME']}:"
        f"{os.environ['MYSQL_PASSWORD']}@localhost:"
        f"{os.environ.get('MYSQL_PORT', 3306)}/{os.environ['MYSQL_DB']}"
    ),
    # Load jwt secret key from credentials file
    "SECRET_KEY": os.environ["JWT_SECRET_KEY"],
    # SQL Alchemy features
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    "JSON_SORT_KEYS": False,
    # Name of the competition to load initiliazition data
    "COMPETITION": COMPETITION,
    "LOCK_DATETIME": config.get("locking", "datetime"),
    "LOCK_DATETIME_FINAL_PHASE": config.get("locking", "datetime_final_phase"),
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
}
