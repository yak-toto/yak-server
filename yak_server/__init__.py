import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict
from strawberry.fastapi import GraphQLRouter

from .helpers.exception_handler import set_exception_handler
from .helpers.logging import setup_logging
from .helpers.profiling import set_yappi_profiler
from .v1.routers.bets import router as bets_router
from .v1.routers.binary_bets import router as binary_bets_router
from .v1.routers.groups import router as groups_router
from .v1.routers.phases import router as phases_router
from .v1.routers.results import router as results_router
from .v1.routers.rules import router as rules_router
from .v1.routers.score_bets import router as score_bets_router
from .v1.routers.teams import router as teams_router
from .v1.routers.users import router as users_router
from .v2 import get_schema
from .v2.context import get_context

logger = logging.getLogger(__name__)

GLOBAL_ENDPOINT = "api"
VERSION1 = "v1"
VERSION2 = "v2"

__version__ = "0.43.1"


class Config(BaseSettings):
    debug: bool = False
    profiling: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


def create_app() -> FastAPI:
    # Initialize fastapi application
    config = Config()

    app = FastAPI(
        debug=config.debug,
        docs_url=f"/{GLOBAL_ENDPOINT}/docs",
        redoc_url=f"/{GLOBAL_ENDPOINT}/redoc",
        openapi_url=f"/{GLOBAL_ENDPOINT}/openapi.json",
    )

    # Include all routers
    v1_prefix = f"/{GLOBAL_ENDPOINT}/{VERSION1}"

    app.include_router(bets_router, prefix=v1_prefix)
    app.include_router(binary_bets_router, prefix=v1_prefix)
    app.include_router(groups_router, prefix=v1_prefix)
    app.include_router(phases_router, prefix=v1_prefix)
    app.include_router(results_router, prefix=v1_prefix)
    app.include_router(rules_router, prefix=v1_prefix)
    app.include_router(score_bets_router, prefix=v1_prefix)
    app.include_router(teams_router, prefix=v1_prefix)
    app.include_router(users_router, prefix=v1_prefix)

    # Set error handler
    set_exception_handler(app)

    # Register graphql endpoint
    graphql_app = GraphQLRouter(
        get_schema(debug=app.debug),
        graphql_ide="apollo-sandbox" if app.debug is True else None,
        context_getter=get_context,
    )

    app.include_router(graphql_app, prefix=f"/{GLOBAL_ENDPOINT}/{VERSION2}", tags=["graphql"])

    # Set CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Declare logger configuration for yak server
    setup_logging(debug=app.debug)

    # Set yappi profiler
    profiling = config.profiling

    if app.debug and profiling:
        set_yappi_profiler(app)

    return app
