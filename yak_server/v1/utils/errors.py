import logging
import traceback
from http import HTTPStatus

from flask import Response, jsonify
from werkzeug.exceptions import HTTPException

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

logger = logging.getLogger(__name__)


class InvalidCredentials(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = INVALID_CREDENTIALS_MESSAGE


class NameAlreadyExists(HTTPException):
    def __init__(self, name) -> None:
        super().__init__(name_already_exists_message(name))
        self.code = HTTPStatus.UNAUTHORIZED


class BetNotFound(HTTPException):
    def __init__(self, bet_id) -> None:
        super().__init__(bet_not_found_message(bet_id))
        self.code = HTTPStatus.NOT_FOUND


class UserNotFound(HTTPException):
    def __init__(self, user_id) -> None:
        super().__init__(user_not_found_message(user_id))
        self.code = HTTPStatus.NOT_FOUND


class UnauthorizedAccessToAdminAPI(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = UNAUTHORIZED_ACCESS_TO_ADMIN_API_MESSAGE


class InvalidTeamId(HTTPException):
    def __init__(self, team_id):
        super().__init__(
            f"Invalid team id: {team_id}. Retry with a uuid or ISO 3166-1 alpha-2 code",
        )
        self.code = HTTPStatus.BAD_REQUEST


class TeamNotFound(HTTPException):
    def __init__(self, team_id):
        super().__init__(team_not_found_message(team_id))
        self.code = HTTPStatus.NOT_FOUND


class LockedScoreBet(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = LOCKED_SCORE_BET_MESSAGE


class LockedBinaryBet(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = LOCKED_BINARY_BET_MESSAGE


class NoResultsForAdminUser(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = "No results for admin user"


class GroupNotFound(HTTPException):
    def __init__(self, group_id) -> None:
        super().__init__(group_not_found_message(group_id))
        self.code = HTTPStatus.NOT_FOUND


class PhaseNotFound(HTTPException):
    def __init__(self, phase_id) -> None:
        super().__init__(phase_not_found_message(phase_id))
        self.code = HTTPStatus.NOT_FOUND


class InvalidToken(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = INVALID_TOKEN_MESSAGE


class ExpiredToken(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = EXPIRED_TOKEN_MESSAGE


class RuleNotFound(HTTPException):
    def __init__(self, rule_id) -> None:
        super().__init__(rule_not_found_message(rule_id))
        self.code = HTTPStatus.NOT_FOUND


class RequestValidationError(HTTPException):
    def __init__(self, schema, path, description):
        super().__init__(description)
        self.schema = schema
        self.path = path
        self.code = HTTPStatus.UNPROCESSABLE_ENTITY


def set_error_handler(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException) -> Response:
        # Return JSON instead of HTML for HTTP errors.
        logger.info(f"Server catches an expected exception: {type(e).__name__} {e.description}")

        return jsonify(ok=False, error_code=e.code, description=e.description), e.code

    @app.errorhandler(Exception)
    def handle_exception(e: Exception) -> Response:
        # Return JSON instead of HTML for generic errors.
        logger.error(traceback.format_exc())
        logger.error(f"An unexcepted expection occurs: {type(e).__name__} {e}")

        return (
            jsonify(
                {
                    "ok": False,
                    "error_code": HTTPStatus.INTERNAL_SERVER_ERROR,
                    "description": f"{type(e).__name__}: {str(e)}"
                    if app.config.get("DEBUG")
                    else "Unexcepted error",
                },
            ),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    @app.errorhandler(RequestValidationError)
    def handle_request_validation_error(e: RequestValidationError) -> Response:
        return (
            jsonify(
                {
                    "ok": False,
                    "error_code": e.code,
                    "description": e.description,
                    "schema": e.schema,
                    "path": list(e.path),
                },
            ),
            e.code,
        )
