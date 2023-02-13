from flask import Response, json
from jwt import ExpiredSignatureError, InvalidTokenError
from werkzeug.exceptions import HTTPException

from .constants import BINARY, SCORE


class InvalidCredentials(HTTPException):
    code = 401
    description = "Invalid credentials"


class NameAlreadyExists(HTTPException):
    def __init__(self, name) -> None:
        super().__init__(f"Name already exists: {name}")
        self.code = 401


class MatchNotFound(HTTPException):
    def __init__(self, match_id) -> None:
        super().__init__(f"Match not found: {match_id}")
        self.code = 404


class BetNotFound(HTTPException):
    def __init__(self, bet_id) -> None:
        super().__init__(f"Bet not found: {bet_id}")
        self.code = 404


class WrongInputs(HTTPException):
    code = 401
    description = "Wrong inputs"


class MissingId(HTTPException):
    code = 401
    description = "Missing id(s) in request"


class UserNotFound(HTTPException):
    code = 404
    description = "User not found"


class NewScoreNegative(HTTPException):
    code = 401
    description = "Score cannot be negative"


class DuplicatedIds(HTTPException):
    def __init__(self, ids) -> None:
        super().__init__(f"Duplicated ids in request: {', '.join(ids)}")
        self.code = 401


class UnauthorizedAccessToAdminAPI(HTTPException):
    code = 401
    description = "Unauthorized access to admin API"


class InvalidTeamId(HTTPException):
    def __init__(self, team_id):
        super().__init__(
            f"Invalid team id: {team_id}. Retry with a uuid or ISO 3166-1 alpha-2 code",
        )
        self.code = 400


class TeamNotFound(HTTPException):
    def __init__(self, team_id):
        super().__init__(f"Team not found: {team_id}")
        self.code = 404


class LockedBets(HTTPException):
    code = 401
    description = "Cannot modify bets because locked date is exceeded"


class InvalidBetType(HTTPException):
    code = 401
    description = f"Invalid bet type. The available bet types are : {SCORE, BINARY}"


class NoResultsForAdminUser(HTTPException):
    code = 401
    description = "No results for admin user"


def set_error_handler(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
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
    def handle_exception(e):
        """Return JSON instead of HTML for generic errors."""

        response = Response()

        response.data = json.dumps(
            {
                "ok": False,
                "error_code": 500,
                "description": f"{type(e).__name__}: {str(e)}"
                if app.config.get("DEBUG")
                else "Unexcepted error",
            },
        )

        response.status_code = 500
        response.content_type = "application/json"

        return response

    @app.errorhandler(ExpiredSignatureError)
    def handler_expired_signature_exception(e):
        response = Response()

        response.data = json.dumps(
            {
                "ok": False,
                "error_code": 401,
                "description": "Expired token. Reauthentication required.",
            },
        )
        response.status_code = 401
        response.content_type = "application/json"

        return response

    @app.errorhandler(InvalidTokenError)
    def handler_invalid_token_exception(e):
        response = Response()

        response.data = json.dumps(
            {
                "ok": False,
                "error_code": 401,
                "description": "Invalid token. Registeration and / or authentication required",
            },
        )
        response.status_code = 401
        response.content_type = "application/json"

        return response
