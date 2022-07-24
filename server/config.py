import json

# Create dummy secrey key so we can use sessions
SECRET_KEY = "d9e886ca-3de1-4382-8a0d-2450f6338fb7"

# Do not sort key in json response
JSON_SORT_KEYS = False

# Create in-memory database
with open("credentials.json") as file:
    config = json.loads(file.read())
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{config['user']}:{config['password']}@localhost:3306/yak_toto"
    )

# SQL Alchemy features
SQLALCHEMY_TRACK_MODIFICATIONS = False
