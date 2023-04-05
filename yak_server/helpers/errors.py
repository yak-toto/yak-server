INVALID_CREDENTIALS_MESSAGE = "Invalid credentials"
UNAUTHORIZED_ACCESS_TO_ADMIN_API_MESSAGE = "Unauthorized access to admin API"
INVALID_TOKEN_MESSAGE = "Invalid token, authentication required"
EXPIRED_TOKEN_MESSAGE = "Expired token, reauthentication required"
LOCKED_SCORE_BET_MESSAGE = "Cannot modify score bet, lock date is exceeded"
LOCKED_BINARY_BET_MESSAGE = "Cannot modify binary bet, lock date is exceeded"


def name_already_exists_message(user_name: str) -> str:
    return f"Name already exists: {user_name}"
