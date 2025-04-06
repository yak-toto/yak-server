import logging
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from strawberry.fastapi import GraphQLRouter

from .helpers.logging_helpers import setup_logging
from .v1.helpers.errors import set_exception_handler
from .v1.routers import bets as bets_router
from .v1.routers import binary_bets as binary_bets_router
from .v1.routers import groups as groups_router
from .v1.routers import phases as phases_router
from .v1.routers import results as results_router
from .v1.routers import rules as rules_router
from .v1.routers import score_bets as score_bets_router
from .v1.routers import teams as teams_router
from .v1.routers import users as users_router
from .v2 import get_schema
from .v2.context import YakContext, get_context

logger = logging.getLogger(__name__)

GLOBAL_ENDPOINT = "api"
VERSION1 = "v1"
VERSION2 = "v2"

__version__ = "0.49.0"


class Config(BaseSettings):
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


class VersionOut(BaseModel):
    version: str

    model_config = ConfigDict(extra="forbid")


def create_app() -> FastAPI:
    # Initialize fastapi application
    config = Config()

    app = FastAPI(
        debug=config.debug,
        docs_url=f"/{GLOBAL_ENDPOINT}/docs",
        redoc_url=f"/{GLOBAL_ENDPOINT}/redoc",
        openapi_url=f"/{GLOBAL_ENDPOINT}/openapi.json",
        version=__version__,
        title="Yak API",
        description="Yak API",
    )

    # Include all routers
    v1_prefix = f"/{GLOBAL_ENDPOINT}/{VERSION1}"

    app.include_router(bets_router.router, prefix=v1_prefix)
    app.include_router(binary_bets_router.router, prefix=v1_prefix)
    app.include_router(groups_router.router, prefix=v1_prefix)
    app.include_router(phases_router.router, prefix=v1_prefix)
    app.include_router(results_router.router, prefix=v1_prefix)
    app.include_router(rules_router.router, prefix=v1_prefix)
    app.include_router(score_bets_router.router, prefix=v1_prefix)
    app.include_router(teams_router.router, prefix=v1_prefix)
    app.include_router(users_router.router, prefix=v1_prefix)

    @app.get(f"/{GLOBAL_ENDPOINT}/version")
    def version() -> VersionOut:
        return VersionOut(version=__version__)

    # Set error handler
    set_exception_handler(app)

    # Register graphql endpoint
    graphql_app = GraphQLRouter[YakContext, Any](
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

    return app
