from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from .telegram_sender import send_message

db = SQLAlchemy()


def create_app():
    send_message("The app is starting")

    app = Flask(__name__)
    app.config.from_pyfile("config.py")
    db.init_app(app)

    from .auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    CORS(app, resources={r"/*": {"origins": "*"}})

    return app
