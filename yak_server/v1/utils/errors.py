import logging
from http import HTTPStatus

from flask import Response, jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class InvalidCredentials(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = "Invalid credentials"


class NameAlreadyExists(HTTPException):
    def __init__(self, name) -> None:
        super().__init__(f"Name already exists: {name}")
        self.code = HTTPStatus.UNAUTHORIZED


class MatchNotFound(HTTPException):
    def __init__(self, match_id) -> None:
        super().__init__(f"Match not found: {match_id}")
        self.code = HTTPStatus.NOT_FOUND


class BetNotFound(HTTPException):
    def __init__(self, bet_id) -> None:
        super().__init__(f"Bet not found: {bet_id}")
        self.code = HTTPStatus.NOT_FOUND


class UserNotFound(HTTPException):
    code = HTTPStatus.NOT_FOUND
    description = "User not found"


class UnauthorizedAccessToAdminAPI(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = "Unauthorized access to admin API"


class InvalidTeamId(HTTPException):
    def __init__(self, team_id):
        super().__init__(
            f"Invalid team id: {team_id}. Retry with a uuid or ISO 3166-1 alpha-2 code",
        )
        self.code = HTTPStatus.BAD_REQUEST


class TeamNotFound(HTTPException):
    def __init__(self, team_id):
        super().__init__(f"Team not found: {team_id}")
        self.code = HTTPStatus.NOT_FOUND


class LockedBets(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = "Cannot modify bets because locked date is exceeded"


class NoResultsForAdminUser(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = "No results for admin user"


class GroupNotFound(HTTPException):
    def __init__(self, group_id) -> None:
        super().__init__(f"Group not found: {group_id}")
        self.code = HTTPStatus.NOT_FOUND


class PhaseNotFound(HTTPException):
    def __init__(self, phase_id) -> None:
        super().__init__(f"Phase not found: {phase_id}")
        self.code = HTTPStatus.NOT_FOUND


class InvalidToken(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = "Invalid token. Registration and / or authentication required"


class ExpiredToken(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = "Expired token. Reauthentication required."


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
