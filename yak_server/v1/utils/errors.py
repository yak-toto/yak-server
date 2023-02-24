from http import HTTPStatus

from flask import Response, json
from jwt import ExpiredSignatureError, InvalidTokenError
from werkzeug.exceptions import HTTPException

from .constants import BINARY, SCORE


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


class WrongInputs(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = "Wrong inputs"


class MissingId(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = "Missing id(s) in request"


class UserNotFound(HTTPException):
    code = HTTPStatus.NOT_FOUND
    description = "User not found"


class NewScoreNegative(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = "Score cannot be negative"


class DuplicatedIds(HTTPException):
    def __init__(self, ids) -> None:
        super().__init__(f"Duplicated ids in request: {', '.join(ids)}")
        self.code = HTTPStatus.UNAUTHORIZED


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


class InvalidBetType(HTTPException):
    code = HTTPStatus.UNAUTHORIZED
    description = f"Invalid bet type. The available bet types are : {SCORE, BINARY}"


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


def set_error_handler(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException) -> Response:
        """Return JSON instead of HTML for HTTP errors."""
        # start with the correct headers and status code from the error
        response = e.get_response()

        # replace the body with JSON
        response.data = json.dumps(
            {
                "ok": False,
                "error_code": e.code,
                "description": e.description,
            },
        )
        response.content_type = "application/json"

        return response

    @app.errorhandler(Exception)
    def handle_exception(e: Exception) -> Response:
        """Return JSON instead of HTML for generic errors."""

        response = Response()

        response.data = json.dumps(
            {
                "ok": False,
                "error_code": HTTPStatus.INTERNAL_SERVER_ERROR,
                "description": f"{type(e).__name__}: {str(e)}"
                if app.config.get("DEBUG")
                else "Unexcepted error",
            },
        )

        response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        response.content_type = "application/json"

        return response

    @app.errorhandler(ExpiredSignatureError)
    def handler_expired_signature_exception(e: ExpiredSignatureError) -> Response:
        response = Response()

        response.data = json.dumps(
            {
                "ok": False,
                "error_code": HTTPStatus.UNAUTHORIZED,
                "description": "Expired token. Reauthentication required.",
            },
        )
        response.status_code = HTTPStatus.UNAUTHORIZED
        response.content_type = "application/json"

        return response

    @app.errorhandler(InvalidTokenError)
    def handler_invalid_token_exception(e: InvalidTokenError) -> Response:
        response = Response()

        response.data = json.dumps(
            {
                "ok": False,
                "error_code": HTTPStatus.UNAUTHORIZED,
                "description": "Invalid token. Registration and / or authentication required",
            },
        )
        response.status_code = HTTPStatus.UNAUTHORIZED
        response.content_type = "application/json"

        return response
