import json
import os
from configparser import ConfigParser
from importlib import resources
from pathlib import Path

with resources.as_file(resources.files("yak_server") / "data" / os.environ["COMPETITION"]) as path:
    DATA_FOLDER = path

config = ConfigParser()
config.read(f"{DATA_FOLDER}/config.ini")

with Path(f"{DATA_FOLDER}/finale_phase_config.json").open() as file:
    FINALE_PHASE_CONFIG = json.loads(file.read())

MYSQL_USER_NAME = os.environ["MYSQL_USER_NAME"]
MYSQL_PASSWORD = os.environ["MYSQL_PASSWORD"]
MYSQL_PORT = os.environ.get("MYSQL_PORT", 3306)
MYSQL_DB = os.environ["MYSQL_DB"]

YAK_CONFIG = {
    # Setup MySQL credentials
    "MYSQL_USER_NAME": MYSQL_USER_NAME,
    "MYSQL_PASSWORD": MYSQL_PASSWORD,
    "MYSQL_PORT": MYSQL_PORT,
    "MYSQL_DB": MYSQL_DB,
    "SQLALCHEMY_DATABASE_URI": (
        f"mysql+pymysql://{MYSQL_USER_NAME}:{MYSQL_PASSWORD}@localhost:{MYSQL_PORT}/{MYSQL_DB}"
    ),
    # Load jwt secret key from credentials file
    "SECRET_KEY": os.environ["JWT_SECRET_KEY"],
    "JWT_EXPIRATION_TIME": int(os.environ["JWT_EXPIRATION_TIME"]),
    # SQL Alchemy features
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
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
