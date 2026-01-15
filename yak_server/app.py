from importlib.metadata import version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict

from . import health_check
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

GLOBAL_ENDPOINT = "api"
VERSION1 = "v1"


class Config(BaseSettings):
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


def create_app() -> FastAPI:
    # Initialize fastapi application
    config = Config()

    app = FastAPI(
        debug=config.debug,
        docs_url=f"/{GLOBAL_ENDPOINT}/docs",
        redoc_url=f"/{GLOBAL_ENDPOINT}/redoc",
        openapi_url=f"/{GLOBAL_ENDPOINT}/openapi.json",
        version=version("yak-server"),
        title="Yak API",
        description="Yak API",
    )

    # Include health check router
    app.include_router(health_check.router, prefix=f"/{GLOBAL_ENDPOINT}")

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

    # Set error handler
    set_exception_handler(app)

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
