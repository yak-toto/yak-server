from typing import List
from uuid import UUID

import strawberry

from yak_server.helpers.errors import (
    EXPIRED_TOKEN_MESSAGE,
    INVALID_CREDENTIALS_MESSAGE,
    INVALID_TOKEN_MESSAGE,
    LOCKED_BINARY_BET_MESSAGE,
    LOCKED_SCORE_BET_MESSAGE,
    UNAUTHORIZED_ACCESS_TO_ADMIN_API_MESSAGE,
    binary_bet_not_found_message,
    group_not_found_message,
    name_already_exists_message,
    phase_not_found_message,
    score_bet_not_found_message,
    team_not_found_message,
    user_not_found_message,
)

from .schema import (
    BinaryBet,
    Group,
    GroupPosition,
    Phase,
    ScoreBet,
    Team,
    User,
    UserWithoutSensitiveInfo,
    UserWithToken,
)


@strawberry.type
class InvalidToken:
    message: str = INVALID_TOKEN_MESSAGE


@strawberry.type
class ExpiredToken:
    message: str = EXPIRED_TOKEN_MESSAGE


@strawberry.type
class UnauthorizedAccessToAdminAPI:
    message: str = UNAUTHORIZED_ACCESS_TO_ADMIN_API_MESSAGE


@strawberry.type
class LockedScoreBetError:
    message: str = LOCKED_SCORE_BET_MESSAGE


@strawberry.type
class ScoreBetNotFoundForUpdate:
    message: str = "Score bet not found. Cannot modify a resource that does not exist."


@strawberry.type
class NewScoreNegative:
    variable_name: strawberry.Private[str]
    score: strawberry.Private[int]

    @strawberry.field
    def message(self) -> str:
        return (
            f"Variable '{self.variable_name}' got invalid value {self.score}. "
            "Score cannot be negative."
        )


ModifyScoreBetResult = strawberry.union(
    "ModifyScoreBetResult",
    types=(
        ScoreBet,
        ScoreBetNotFoundForUpdate,
        LockedScoreBetError,
        NewScoreNegative,
        InvalidToken,
        ExpiredToken,
    ),
)


@strawberry.type
class LockedBinaryBetError:
    message: str = LOCKED_BINARY_BET_MESSAGE


@strawberry.type
class BinaryBetNotFoundForUpdate:
    message: str = "Binary bet not found. Cannot modify a resource that does not exist."


ModifyBinaryBetResult = strawberry.union(
    "ModifyBinaryBetResult",
    types=(
        BinaryBet,
        BinaryBetNotFoundForUpdate,
        LockedBinaryBetError,
        InvalidToken,
        ExpiredToken,
    ),
)


CurrentUserResult = strawberry.union("CurrentUserResult", types=(User, InvalidToken, ExpiredToken))


@strawberry.type
class AllTeamsSuccessful:
    teams: List[Team]


AllTeamsResult = strawberry.union(
    "AllTeamsResult",
    types=(AllTeamsSuccessful, InvalidToken, ExpiredToken),
)


@strawberry.type
class TeamByIdNotFound:
    id: strawberry.Private[UUID]

    @strawberry.field
    def message(self) -> str:
        return team_not_found_message(self.id)


@strawberry.type
class TeamByCodeNotFound:
    code: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return team_not_found_message(self.code)


TeamByIdResult = strawberry.union(
    "TeamByIdResult",
    types=(Team, TeamByIdNotFound, InvalidToken, ExpiredToken),
)
TeamByCodeResult = strawberry.union(
    "TeamByCodeResult",
    types=(Team, TeamByCodeNotFound, InvalidToken, ExpiredToken),
)


@strawberry.type
class ScoreBetNotFound:
    id: strawberry.Private[UUID]

    @strawberry.field
    def message(self) -> str:
        return score_bet_not_found_message(self.id)


ScoreBetResult = strawberry.union(
    "ScoreBetResult",
    types=(ScoreBet, ScoreBetNotFound, InvalidToken, ExpiredToken),
)


@strawberry.type
class BinaryBetNotFound:
    id: strawberry.Private[UUID]

    @strawberry.field
    def message(self) -> str:
        return binary_bet_not_found_message(self.id)


BinaryBetResult = strawberry.union(
    "BinaryBetResult",
    types=(
        BinaryBet,
        BinaryBetNotFound,
        InvalidToken,
        ExpiredToken,
    ),
)


@strawberry.type
class Groups:
    groups: List[Group]


AllGroupsResult = strawberry.union("AllGroupsResult", types=(Groups, InvalidToken, ExpiredToken))


@strawberry.type
class GroupByCodeNotFound:
    code: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return group_not_found_message(self.code)


GroupByCodeResult = strawberry.union(
    "GroupByCodeResult",
    types=(Group, GroupByCodeNotFound, InvalidToken, ExpiredToken),
)


@strawberry.type
class GroupByIdNotFound:
    id: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return group_not_found_message(self.id)


GroupByIdResult = strawberry.union(
    "GroupByIdResult",
    types=(Group, GroupByIdNotFound, InvalidToken, ExpiredToken),
)


@strawberry.type
class Phases:
    phases: List[Phase]


AllPhasesResult = strawberry.union("AllPhasesResult", types=(Phases, InvalidToken, ExpiredToken))


@strawberry.type
class PhaseByCodeNotFound:
    code: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return phase_not_found_message(self.code)


PhaseByCodeResult = strawberry.union(
    "PhaseByCodeResult",
    types=(Phase, PhaseByCodeNotFound, InvalidToken, ExpiredToken),
)


@strawberry.type
class PhaseByIdNotFound:
    id: strawberry.Private[UUID]

    @strawberry.field
    def message(self) -> str:
        return phase_not_found_message(self.id)


PhaseByIdResult = strawberry.union(
    "PhaseByIdResult",
    types=(Phase, PhaseByIdNotFound, InvalidToken, ExpiredToken),
)


@strawberry.type
class ScoreBoard:
    users: List[UserWithoutSensitiveInfo]


ScoreBoardResult = strawberry.union(
    "ScoreBoardResult",
    types=(ScoreBoard, InvalidToken, ExpiredToken),
)


@strawberry.type
class UserNameAlreadyExists:
    user_name: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return name_already_exists_message(self.user_name)


SignupResult = strawberry.union("SignupResult", types=(UserWithToken, UserNameAlreadyExists))


@strawberry.type
class InvalidCredentials:
    message: str = INVALID_CREDENTIALS_MESSAGE


LoginResult = strawberry.union("LoginResult", types=(UserWithToken, InvalidCredentials))


@strawberry.type
class GroupRank:
    group_rank: List[GroupPosition]
    group: Group


GroupRankByCodeResult = strawberry.union(
    "GroupRankByCodeResult",
    types=(GroupRank, GroupByCodeNotFound, InvalidToken, ExpiredToken),
)


GroupRankByIdResult = strawberry.union(
    "GroupRankByIdResult",
    types=(GroupRank, GroupByIdNotFound, InvalidToken, ExpiredToken),
)


@strawberry.type
class UserNotFound:
    id: strawberry.Private[UUID]

    @strawberry.field
    def message(self) -> str:
        return user_not_found_message(self.id)


ModifyUserResult = strawberry.union(
    "ModifyUserResult",
    types=(
        UserWithoutSensitiveInfo,
        UserNotFound,
        InvalidToken,
        ExpiredToken,
        UnauthorizedAccessToAdminAPI,
    ),
)
