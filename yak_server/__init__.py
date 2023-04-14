import logging
import sys

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources

from flask import Flask
from flask.cli import load_dotenv
from flask_cors import CORS
from flask_migrate import Migrate
from strawberry.flask.views import GraphQLView

from .database.models import get_db

logger = logging.getLogger(__name__)

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)

    with resources.as_file(resources.files("yak_server") / "database/migrations") as path:
        Migrate(app, get_db(), directory=path)

    # Configuration setup
    from .config_file import get_config

    app.config.from_mapping(get_config())
    app.json.sort_keys = False

    app.db = get_db()

    # --------------------------------------------- #
    # Version 1 setup (REST api)
    # --------------------------------------------- #

    # Registrer error handler
    from .v1.utils.errors import set_error_handler

    set_error_handler(app)

    # Registrer blueprint
    from .v1.auth import auth as auth_blueprint
    from .v1.bets import bets as bets_blueprint
    from .v1.binary_bets import binary_bets as binary_bets_blueprint
    from .v1.groups import groups as groups_blueprint
    from .v1.phase import phase as phase_blueprint
    from .v1.results import results as results_blueprint
    from .v1.rules import rules as rules_blueprint
    from .v1.score_bets import score_bets as score_bets_blueprint
    from .v1.teams import teams as teams_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(bets_blueprint)
    app.register_blueprint(binary_bets_blueprint)
    app.register_blueprint(groups_blueprint)
    app.register_blueprint(phase_blueprint)
    app.register_blueprint(results_blueprint)
    app.register_blueprint(rules_blueprint)
    app.register_blueprint(score_bets_blueprint)
    app.register_blueprint(teams_blueprint)

    # --------------------------------------------- #
    # Version 2 setup (GraphQL api)
    # --------------------------------------------- #
    from .v2 import schema
    from .v2.utils.constants import GLOBAL_ENDPOINT, VERSION

    # Registrer endpoint
    app.add_url_rule(
        f"/{GLOBAL_ENDPOINT}/{VERSION}",
        view_func=GraphQLView.as_view("graphql_view", schema=schema, graphiql=app.config["DEBUG"]),
    )

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # --------------------------------------------- #
    # Declare logger configuration for yak server
    # --------------------------------------------- #
    logging.basicConfig(
        filename="yak.log",
        level=logging.DEBUG if app.config.get("DEBUG") else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Start yak flask server")

    return app
