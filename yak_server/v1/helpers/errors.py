import logging

from fastapi import status

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
from yak_server.helpers.exception_handler import APIVersion1Error

logger = logging.getLogger(__name__)


class InvalidCredentials(APIVersion1Error):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_MESSAGE,
        )


class NameAlreadyExists(APIVersion1Error):
    def __init__(self, name: str) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=name_already_exists_message(name),
        )


class BetNotFound(APIVersion1Error):
    def __init__(self, bet_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=bet_not_found_message(bet_id),
        )


class UnsatisfiedPasswordRequirements(APIVersion1Error):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsatisfied password requirements. {detail}",
        )


class UserNotFound(APIVersion1Error):
    def __init__(self, user_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=user_not_found_message(user_id),
        )


class UnauthorizedAccessToAdminAPI(APIVersion1Error):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=UNAUTHORIZED_ACCESS_TO_ADMIN_API_MESSAGE,
        )


class InvalidTeamId(APIVersion1Error):
    def __init__(self, team_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid team id: {team_id}. Retry with a uuid or ISO 3166-1 alpha-2 code",
        )


class TeamNotFound(APIVersion1Error):
    def __init__(self, team_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=team_not_found_message(team_id),
        )


class LockedScoreBet(APIVersion1Error):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=LOCKED_SCORE_BET_MESSAGE)


class LockedBinaryBet(APIVersion1Error):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=LOCKED_BINARY_BET_MESSAGE)


class NoResultsForAdminUser(APIVersion1Error):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No results for admin user",
        )


class GroupNotFound(APIVersion1Error):
    def __init__(self, group_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=group_not_found_message(group_id),
        )


class PhaseNotFound(APIVersion1Error):
    def __init__(self, phase_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=phase_not_found_message(phase_id),
        )


class InvalidToken(APIVersion1Error):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN_MESSAGE)


class ExpiredToken(APIVersion1Error):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=EXPIRED_TOKEN_MESSAGE)


class RuleNotFound(APIVersion1Error):
    def __init__(self, rule_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rule_not_found_message(rule_id),
        )
