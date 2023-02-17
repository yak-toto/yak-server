from flask import Flask
from flask.cli import load_dotenv
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from strawberry.flask.views import GraphQLView

db = SQLAlchemy()

load_dotenv()


def create_app():
    app = Flask(__name__)

    # Configuration setup
    from .config_file import YAK_CONFIG

    app.config.from_mapping(YAK_CONFIG)
    app.json.sort_keys = False

    # Database setup
    db.init_app(app)

    # --------------------------------------------- #
    # Version 1 setup (REST api)
    # --------------------------------------------- #

    # Registrer error handler
    from .v1.utils.errors import set_error_handler

    set_error_handler(app)

    # Registrer blueprint
    from .v1.auth import auth as auth_blueprint
    from .v1.bets import bets as bets_blueprint
    from .v1.config import config as config_blueprint
    from .v1.groups import groups as groups_blueprint
    from .v1.matches import matches as matches_blueprint
    from .v1.results import results as results_blueprint
    from .v1.teams import teams as teams_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(bets_blueprint)
    app.register_blueprint(config_blueprint)
    app.register_blueprint(results_blueprint)
    app.register_blueprint(groups_blueprint)
    app.register_blueprint(matches_blueprint)
    app.register_blueprint(teams_blueprint)

    # --------------------------------------------- #
    # Version 2 setup (GraphQL api)
    # --------------------------------------------- #
    from .v2 import schema
    from .v2.utils.constants import GLOBAL_ENDPOINT, VERSION

    # Registrer endpoint
    app.add_url_rule(
        f"/{GLOBAL_ENDPOINT}/{VERSION}",
        view_func=GraphQLView.as_view("graphql_view", schema=schema),
    )

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # --------------------------------------------- #
    # CLI setup (flask db create|init|delete|admin)
    # --------------------------------------------- #
    from .cli import db_cli

    app.cli.add_command(db_cli)

    return app
