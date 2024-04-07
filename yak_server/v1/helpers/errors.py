import logging
import traceback
from typing import TYPE_CHECKING

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


def set_exception_handler(app: "FastAPI") -> None:
    @app.exception_handler(StarletteHTTPException)
    def http_exception_handler(_: Request, http_exception: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=http_exception.status_code,
            content={
                "ok": False,
                "error_code": http_exception.status_code,
                "description": http_exception.detail,
            },
        )

    @app.exception_handler(Exception)
    def handle_exception(_: Request, exception: Exception) -> JSONResponse:  # pragma: no cover
        # Return JSON instead of HTML for generic errors.
        logger.error(traceback.format_exc())
        logger.error(f"An unexpected exception occurs: {type(exception).__name__} {exception}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "ok": False,
                "error_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "description": (
                    f"{type(exception).__name__}: {exception!s}"
                    if app.debug
                    else "Unexpected error"
                ),
            },
        )

    @app.exception_handler(RequestValidationError)
    def request_validator_error_handler(
        _: Request,
        request_validator_error: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "ok": False,
                "error_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "description": request_validator_error.errors(),
            },
        )
