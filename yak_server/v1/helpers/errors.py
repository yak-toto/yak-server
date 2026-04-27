import logging
import traceback
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from yak_server.helpers.errors import (
    EXPIRED_REFRESH_TOKEN_MESSAGE,
    EXPIRED_TOKEN_MESSAGE,
    INVALID_CREDENTIALS_MESSAGE,
    INVALID_REFRESH_TOKEN_MESSAGE,
    INVALID_TOKEN_MESSAGE,
    LOCKED_BINARY_BET_MESSAGE,
    LOCKED_SCORE_BET_MESSAGE,
    RATE_LIMIT_EXCEEDED_MESSAGE,
    UNAUTHORIZED_ACCESS_TO_ADMIN_API_MESSAGE,
    ErrorCode,
    bet_not_found_message,
    group_not_found_message,
    name_already_exists_message,
    phase_not_found_message,
    rule_not_found_message,
    team_flag_not_found_message,
    team_not_found_message,
    user_not_found_message,
)

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


class YakHTTPException(Exception):  # noqa: N818
    def __init__(self, status_code: int, detail: str, error_code: ErrorCode) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code


class InvalidCredentials(YakHTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_MESSAGE,
            error_code=ErrorCode.INVALID_CREDENTIALS,
        )


class NameAlreadyExists(YakHTTPException):
    def __init__(self, name: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=name_already_exists_message(name),
            error_code=ErrorCode.NAME_ALREADY_EXISTS,
        )


class BetNotFound(YakHTTPException):
    def __init__(self, bet_id: UUID) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=bet_not_found_message(bet_id),
            error_code=ErrorCode.BET_NOT_FOUND,
        )


class UnsatisfiedPasswordRequirements(YakHTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsatisfied password requirements. {detail}",
            error_code=ErrorCode.UNSATISFIED_PASSWORD_REQUIREMENTS,
        )


class UserNotFound(YakHTTPException):
    def __init__(self, user_id: UUID) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=user_not_found_message(user_id),
            error_code=ErrorCode.USER_NOT_FOUND,
        )


class UnauthorizedAccessToAdminAPI(YakHTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=UNAUTHORIZED_ACCESS_TO_ADMIN_API_MESSAGE,
            error_code=ErrorCode.UNAUTHORIZED_ACCESS_TO_ADMIN_API,
        )


class NoAdminUser(YakHTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No admin user found",
            error_code=ErrorCode.NO_ADMIN_USER,
        )


class TeamNotFound(YakHTTPException):
    def __init__(self, team_id: str | UUID) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=team_not_found_message(team_id),
            error_code=ErrorCode.TEAM_NOT_FOUND,
        )


class TeamFlagNotFound(YakHTTPException):
    def __init__(self, team_id: str | UUID) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=team_flag_not_found_message(team_id),
            error_code=ErrorCode.TEAM_FLAG_NOT_FOUND,
        )


class LockedScoreBet(YakHTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=LOCKED_SCORE_BET_MESSAGE,
            error_code=ErrorCode.LOCKED_SCORE_BET,
        )


class LockedBinaryBet(YakHTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=LOCKED_BINARY_BET_MESSAGE,
            error_code=ErrorCode.LOCKED_BINARY_BET,
        )


class GroupNotFound(YakHTTPException):
    def __init__(self, group_id: str | UUID) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=group_not_found_message(group_id),
            error_code=ErrorCode.GROUP_NOT_FOUND,
        )


class PhaseNotFound(YakHTTPException):
    def __init__(self, phase_id: str | UUID) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=phase_not_found_message(phase_id),
            error_code=ErrorCode.PHASE_NOT_FOUND,
        )


class InvalidToken(YakHTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_TOKEN_MESSAGE,
            error_code=ErrorCode.INVALID_TOKEN,
        )


class ExpiredToken(YakHTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=EXPIRED_TOKEN_MESSAGE,
            error_code=ErrorCode.EXPIRED_TOKEN,
        )


class InvalidRefreshToken(YakHTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_REFRESH_TOKEN_MESSAGE,
            error_code=ErrorCode.INVALID_REFRESH_TOKEN,
        )


class ExpiredRefreshToken(YakHTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=EXPIRED_REFRESH_TOKEN_MESSAGE,
            error_code=ErrorCode.EXPIRED_REFRESH_TOKEN,
        )


class RuleNotFound(YakHTTPException):
    def __init__(self, rule_id: UUID) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rule_not_found_message(rule_id),
            error_code=ErrorCode.RULE_NOT_FOUND,
        )


class RateLimitExceeded(YakHTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=RATE_LIMIT_EXCEEDED_MESSAGE,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
        )


def log_traceback(exception: Exception) -> None:
    """
    Log the traceback of an exception.
    """
    for frame in traceback.format_list(traceback.extract_tb(exception.__traceback__)):
        logger.info(frame)

    if exception.__cause__:
        for frame in traceback.format_list(traceback.extract_tb(exception.__cause__.__traceback__)):
            logger.info(frame)


def set_exception_handler(app: "FastAPI") -> None:
    @app.exception_handler(StarletteHTTPException)
    def http_exception_handler(_: Request, http_exception: StarletteHTTPException) -> JSONResponse:
        log_traceback(http_exception)

        logger.info(
            f"An expected exception occurs: {type(http_exception).__name__} {http_exception}",
        )

        return JSONResponse(
            status_code=http_exception.status_code,
            content={
                "ok": False,
                "error_code": ErrorCode.HTTP_EXCEPTION,
                "description": http_exception.detail,
            },
        )

    @app.exception_handler(Exception)
    def handle_exception(_: Request, exception: Exception) -> JSONResponse:  # pragma: no cover
        # Return JSON instead of HTML for generic errors.
        log_traceback(exception)

        logger.error(f"An unexpected exception occurs: {type(exception).__name__} {exception}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "ok": False,
                "error_code": ErrorCode.INTERNAL_SERVER_ERROR,
                "description": (
                    f"{type(exception).__name__}: {exception!s}"
                    if app.debug
                    else "Unexpected error"
                ),
            },
        )

    @app.exception_handler(YakHTTPException)
    def yak_http_exception_handler(
        _: Request, yak_http_exception: YakHTTPException
    ) -> JSONResponse:
        log_traceback(yak_http_exception)

        logger.info(
            "An expected exception occurs:"
            f" {type(yak_http_exception).__name__} {yak_http_exception}",
        )

        return JSONResponse(
            status_code=yak_http_exception.status_code,
            content={
                "ok": False,
                "error_code": yak_http_exception.error_code,
                "description": yak_http_exception.detail,
            },
        )

    @app.exception_handler(RequestValidationError)
    def request_validator_error_handler(
        _: Request,
        request_validator_error: RequestValidationError,
    ) -> JSONResponse:
        log_traceback(request_validator_error)

        logger.info(
            "An validation error occurs: "
            f"{type(request_validator_error).__name__} {request_validator_error}",
        )

        errors = []

        for err in request_validator_error.errors():
            loc = " -> ".join(str(loc) for loc in err["loc"])
            msg = err["msg"]
            errors.append({"field": loc, "error": msg})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "ok": False,
                "error_code": ErrorCode.VALIDATION_ERROR,
                "description": errors,
            },
        )

    @app.exception_handler(SQLAlchemyError)
    def sql_alchemy_error_handler(_: Request, sql_alchemy_error: SQLAlchemyError) -> JSONResponse:
        log_traceback(sql_alchemy_error)

        logger.error(f"Database error: {type(sql_alchemy_error).__name__} {sql_alchemy_error}")

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "ok": False,
                "error_code": ErrorCode.SERVICE_UNAVAILABLE,
                "description": "Service Unavailable",
            },
        )
