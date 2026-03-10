from functools import partial
from uuid import UUID

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
user_not_found_message = partial(generic_not_found_message, resource_name="User")
