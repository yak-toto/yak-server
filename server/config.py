import json

# Do not sort key in json response
JSON_SORT_KEYS = False

# Read secret infos
with open("credentials.json") as file:
    config = json.loads(file.read())
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{config['user']}:{config['password']}@localhost:3306/yak_toto"
    )

    # Load jwt secret key from credentials file
    SECRET_KEY = config["secret_key"]

# SQL Alchemy features
SQLALCHEMY_TRACK_MODIFICATIONS = False
