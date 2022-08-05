import datetime

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.flask_utils import success_response

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile("config.py")
    db.init_app(app)

    # Registrer blueprint
    from .auth import auth as auth_blueprint
    from .bets import bets as bets_blueprint
    from .results import results as results_blueprint
    from .groups import groups as groups_blueprint
    from .final_phase import final_phase as final_phase_blueprint
    from .teams import teams as teams_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(bets_blueprint)
    app.register_blueprint(results_blueprint)
    app.register_blueprint(groups_blueprint)
    app.register_blueprint(final_phase_blueprint)
    app.register_blueprint(teams_blueprint)

    @app.route(f"/{GLOBAL_ENDPOINT}/{VERSION}")
    def ping():
        return success_response(200, {"datetime": datetime.datetime.now()})

    CORS(app, resources={r"/*": {"origins": "*"}})

    return app
