import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.config import Config
from strawberry.fastapi import GraphQLRouter

from .helpers.logging import setup_logging

logger = logging.getLogger(__name__)

GLOBAL_ENDPOINT = "api"
VERSION1 = "v1"
VERSION2 = "v2"

__version__ = "0.38.1"


def create_app() -> FastAPI:
    # Initialize fastapi application
    config = Config(".env")

    app = FastAPI(
        debug=config("DEBUG", cast=bool, default=False),
        docs_url=f"/{GLOBAL_ENDPOINT}/docs",
        redoc_url=f"/{GLOBAL_ENDPOINT}/redoc",
        openapi_url=f"/{GLOBAL_ENDPOINT}/openapi.json",
    )

    # Include all routers
    from .v1.routers import bets as bets_router
    from .v1.routers import binary_bets as binary_bets_router
    from .v1.routers import groups as groups_router
    from .v1.routers import phases as phases_router
    from .v1.routers import results as results_router
    from .v1.routers import rules as rules_router
    from .v1.routers import score_bets as score_bets_router
    from .v1.routers import teams as teams_router
    from .v1.routers import users as users_router

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
    from .v1.helpers.errors import set_exception_handler

    set_exception_handler(app)

    # Register graphql endpoint
    from .v2 import get_schema
    from .v2.context import get_context

    if sys.version_info >= (3, 8):
        graphql_app = GraphQLRouter(
            get_schema(debug=app.debug),
            graphql_ide="apollo-sandbox" if app.debug is True else None,
            context_getter=get_context,
        )
    else:
        # The breaking change introduced in strawberry 0.213.0
        # (link: https://strawberry.rocks/docs/breaking-changes/0.213.0) is not appliable
        # for python 3.7.
        graphql_app = GraphQLRouter(
            get_schema(debug=app.debug),
            graphiql=app.debug,
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
    profiling = config("PROFILING", cast=bool, default=False)

    if app.debug and profiling:
        from .helpers.profiling import set_yappi_profiler

        set_yappi_profiler(app)

    return app
