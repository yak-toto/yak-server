# Create dummy secrey key so we can use sessions
SECRET_KEY = 'd9e886ca-3de1-4382-8a0d-2450f6338fb7'

# Create in-memory database
DATABASE_FILE = 'db.sqlite'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE_FILE
SQLALCHEMY_ECHO = True

# SQL Alchemy features
SQLALCHEMY_TRACK_MODIFICATIONS = False