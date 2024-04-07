import logging
from functools import partial

from fastapi import HTTPException, status

INVALID_CREDENTIALS_MESSAGE = "Invalid credentials"
UNAUTHORIZED_ACCESS_TO_ADMIN_API_MESSAGE = "Unauthorized access to admin API"
INVALID_TOKEN_MESSAGE = "Invalid token, authentication required"
EXPIRED_TOKEN_MESSAGE = "Expired token, re-authentication required"
LOCKED_SCORE_BET_MESSAGE = "Cannot modify score bet, lock date is exceeded"
LOCKED_BINARY_BET_MESSAGE = "Cannot modify binary bet, lock date is exceeded"


def name_already_exists_message(user_name: str) -> str:
    return f"Name already exists: {user_name}"


def generic_not_found_message(id: str, resource_name: str) -> str:
    return f"{resource_name} not found: {id}"


bet_not_found_message = partial(generic_not_found_message, resource_name="Bet")
binary_bet_not_found_message = partial(generic_not_found_message, resource_name="Binary bet")
group_not_found_message = partial(generic_not_found_message, resource_name="Group")
phase_not_found_message = partial(generic_not_found_message, resource_name="Phase")
rule_not_found_message = partial(generic_not_found_message, resource_name="Rule")
score_bet_not_found_message = partial(generic_not_found_message, resource_name="Score bet")
team_not_found_message = partial(generic_not_found_message, resource_name="Team")
user_not_found_message = partial(generic_not_found_message, resource_name="User")


logger = logging.getLogger(__name__)


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


class RuleNotFound(HTTPException):
    def __init__(self, rule_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rule_not_found_message(rule_id),
        )


class ExpiredToken(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=EXPIRED_TOKEN_MESSAGE)


class InvalidToken(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN_MESSAGE)


class UnauthorizedAccessToAdminAPI(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=UNAUTHORIZED_ACCESS_TO_ADMIN_API_MESSAGE,
        )


class UserNotFound(HTTPException):
    def __init__(self, user_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=user_not_found_message(user_id),
        )


class InvalidCredentials(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_MESSAGE,
        )


class NameAlreadyExistsError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(name_already_exists_message(name))
