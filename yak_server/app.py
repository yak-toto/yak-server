from importlib.metadata import version

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict

from yak_server.v1.helpers.rate_limiting import global_rate_limit, limiter

from . import health_check
from .helpers.logging_helpers import setup_logging
from .helpers.settings import CookieSettings
from .v1.helpers.errors import set_exception_handler
from .v1.router import router as v1_router
from .v1.routers import version as version_router

GLOBAL_ENDPOINT = "api"


class Config(BaseSettings):
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


def create_app() -> FastAPI:
    # Initialize fastapi application
    config = Config()

    # Only expose the interactive docs and OpenAPI schema when running in debug mode.
    # In production this avoids publishing the full API surface (and server version).
    app = FastAPI(
        debug=config.debug,
        docs_url=f"/{GLOBAL_ENDPOINT}/docs" if config.debug else None,
        redoc_url=f"/{GLOBAL_ENDPOINT}/redoc" if config.debug else None,
        openapi_url=f"/{GLOBAL_ENDPOINT}/openapi.json" if config.debug else None,
        version=version("yak-server"),
        title="Yak API",
        description="Yak API",
        dependencies=[Depends(global_rate_limit)],
    )

    app.state.limiter = limiter

    api_router = APIRouter(prefix=f"/{GLOBAL_ENDPOINT}")
    api_router.include_router(health_check.router)
    api_router.include_router(version_router.router)
    api_router.include_router(v1_router)

    app.include_router(api_router)

    # Set error handler
    set_exception_handler(app)

    # Set CORS
    cookie_settings = CookieSettings()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cookie_settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Declare logger configuration for yak server
    setup_logging(debug=app.debug)

    return app
