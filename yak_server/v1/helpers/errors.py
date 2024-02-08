import logging
import traceback
from typing import TYPE_CHECKING

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from yak_server.helpers.errors import (
    EXPIRED_TOKEN_MESSAGE,
    INVALID_CREDENTIALS_MESSAGE,
    INVALID_TOKEN_MESSAGE,
    LOCKED_BINARY_BET_MESSAGE,
    LOCKED_SCORE_BET_MESSAGE,
    UNAUTHORIZED_ACCESS_TO_ADMIN_API_MESSAGE,
    bet_not_found_message,
    group_not_found_message,
    name_already_exists_message,
    phase_not_found_message,
    rule_not_found_message,
    team_not_found_message,
    user_not_found_message,
)

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


class InvalidCredentials(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_MESSAGE,
        )


class NameAlreadyExists(HTTPException):
    def __init__(self, name: str) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=name_already_exists_message(name),
        )


class BetNotFound(HTTPException):
    def __init__(self, bet_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=bet_not_found_message(bet_id),
        )


class UnsatisfiedPasswordRequirements(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsatisfied password requirements. {detail}",
        )


class UserNotFound(HTTPException):
    def __init__(self, user_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=user_not_found_message(user_id),
        )


class UnauthorizedAccessToAdminAPI(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=UNAUTHORIZED_ACCESS_TO_ADMIN_API_MESSAGE,
        )


class InvalidTeamId(HTTPException):
    def __init__(self, team_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid team id: {team_id}. Retry with a uuid or ISO 3166-1 alpha-2 code",
        )


class TeamNotFound(HTTPException):
    def __init__(self, team_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=team_not_found_message(team_id),
        )


class LockedScoreBet(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=LOCKED_SCORE_BET_MESSAGE)


class LockedBinaryBet(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=LOCKED_BINARY_BET_MESSAGE)


class NoResultsForAdminUser(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No results for admin user",
        )


class GroupNotFound(HTTPException):
    def __init__(self, group_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=group_not_found_message(group_id),
        )


class PhaseNotFound(HTTPException):
    def __init__(self, phase_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=phase_not_found_message(phase_id),
        )


class InvalidToken(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN_MESSAGE)


class ExpiredToken(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=EXPIRED_TOKEN_MESSAGE)


class RuleNotFound(HTTPException):
    def __init__(self, rule_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rule_not_found_message(rule_id),
        )


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
