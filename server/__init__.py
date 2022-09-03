from flask import Flask
from flask.cli import load_dotenv
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile("config_file.py")
    db.init_app(app)

    # Registrer blueprint
    from .auth import auth as auth_blueprint
    from .config import config as config_blueprint
    from .bets import bets as bets_blueprint
    from .results import results as results_blueprint
    from .groups import groups as groups_blueprint
    from .final_phase import final_phase as final_phase_blueprint
    from .teams import teams as teams_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(bets_blueprint)
    app.register_blueprint(config_blueprint)
    app.register_blueprint(results_blueprint)
    app.register_blueprint(groups_blueprint)
    app.register_blueprint(final_phase_blueprint)
    app.register_blueprint(teams_blueprint)

    CORS(app, resources={r"/*": {"origins": "*"}})

    return app
