from enum import Enum
from functools import partial
from uuid import UUID


class ErrorCode(str, Enum):
    # Authentication
    INVALID_CREDENTIALS = "invalid_credentials"
    UNAUTHORIZED_ACCESS_TO_ADMIN_API = "unauthorized_access_to_admin_api"
    NO_ADMIN_USER = "no_admin_user"
    INVALID_TOKEN = "invalid_token"
    EXPIRED_TOKEN = "expired_token"
    INVALID_REFRESH_TOKEN = "invalid_refresh_token"
    EXPIRED_REFRESH_TOKEN = "expired_refresh_token"

    # Users
    NAME_ALREADY_EXISTS = "name_already_exists"
    USER_NOT_FOUND = "user_not_found"
    UNSATISFIED_PASSWORD_REQUIREMENTS = "unsatisfied_password_requirements"

    # Bets
    BET_NOT_FOUND = "bet_not_found"
    LOCKED_SCORE_BET = "locked_score_bet"
    LOCKED_BINARY_BET = "locked_binary_bet"

    # Resources
    TEAM_NOT_FOUND = "team_not_found"
    TEAM_FLAG_NOT_FOUND = "team_flag_not_found"
    INVALID_TEAM_ID = "invalid_team_id"
    GROUP_NOT_FOUND = "group_not_found"
    PHASE_NOT_FOUND = "phase_not_found"
    RULE_NOT_FOUND = "rule_not_found"

    # Generic
    VALIDATION_ERROR = "validation_error"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    HTTP_EXCEPTION = "http_exception"


INVALID_CREDENTIALS_MESSAGE = "Invalid credentials"
UNAUTHORIZED_ACCESS_TO_ADMIN_API_MESSAGE = "Unauthorized access to admin API"
INVALID_TOKEN_MESSAGE = "Invalid access token, authentication required"
EXPIRED_TOKEN_MESSAGE = "Expired access token, re-authentication required"
INVALID_REFRESH_TOKEN_MESSAGE = "Invalid refresh token, re-authentication required"
EXPIRED_REFRESH_TOKEN_MESSAGE = "Expired refresh token, re-authentication required"
LOCKED_SCORE_BET_MESSAGE = "Cannot modify score bet, lock date is exceeded"
LOCKED_BINARY_BET_MESSAGE = "Cannot modify binary bet, lock date is exceeded"
RATE_LIMIT_EXCEEDED_MESSAGE = "Rate limit exceeded. Please try again later."


def name_already_exists_message(user_name: str) -> str:
    return f"Name already exists: {user_name}"


def generic_not_found_message(resource_id: UUID | str, resource_name: str) -> str:
    return f"{resource_name} not found: {resource_id}"


bet_not_found_message = partial(generic_not_found_message, resource_name="Bet")
binary_bet_not_found_message = partial(generic_not_found_message, resource_name="Binary bet")
group_not_found_message = partial(generic_not_found_message, resource_name="Group")
phase_not_found_message = partial(generic_not_found_message, resource_name="Phase")
rule_not_found_message = partial(generic_not_found_message, resource_name="Rule")
score_bet_not_found_message = partial(generic_not_found_message, resource_name="Score bet")
team_not_found_message = partial(generic_not_found_message, resource_name="Team")
team_flag_not_found_message = partial(generic_not_found_message, resource_name="Team flag")
user_not_found_message = partial(generic_not_found_message, resource_name="User")
