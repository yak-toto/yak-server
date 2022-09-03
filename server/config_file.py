import os

# Do not sort key in json response
JSON_SORT_KEYS = False

# Setup MySQL credentials
SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{os.environ['MYSQL_USER_NAME']}:"
    f"{os.environ['MYSQL_PASSWORD']}@localhost:3306/yak_toto"
)

# Load jwt secret key from credentials file
SECRET_KEY = os.environ["JWT_SECRET_KEY"]

# SQL Alchemy features
SQLALCHEMY_TRACK_MODIFICATIONS = False


def load_business_rules():
    from configparser import ConfigParser

    config = ConfigParser()
    config.read("data/config.ini")
    return config


config = load_business_rules()

LOCK_DATETIME = config.get("locking", "datetime")
BASE_CORRECT_RESULT = config.getint("points", "base_correct_result")
MULTIPLYING_FACTOR_CORRECT_RESULT = config.getint(
    "points", "multiplying_factor_correct_result"
)
BASE_CORRECT_SCORE = config.getint("points", "base_correct_score")
MULTIPLYING_FACTOR_CORRECT_SCORE = config.getint(
    "points", "multiplying_factor_correct_score"
)
