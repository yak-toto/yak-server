from typing import Annotated, Union
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


ModifyScoreBetResult = Annotated[
    Union[
        ScoreBet,
        ScoreBetNotFoundForUpdate,
        LockedScoreBetError,
        NewScoreNegative,
        InvalidToken,
        ExpiredToken,
    ],
    strawberry.union("ModifyScoreBetResult"),
]


@strawberry.type
class LockedBinaryBetError:
    message: str = LOCKED_BINARY_BET_MESSAGE


@strawberry.type
class BinaryBetNotFoundForUpdate:
    message: str = "Binary bet not found. Cannot modify a resource that does not exist."


ModifyBinaryBetResult = Annotated[
    Union[
        BinaryBet,
        BinaryBetNotFoundForUpdate,
        LockedBinaryBetError,
        InvalidToken,
        ExpiredToken,
    ],
    strawberry.union("ModifyBinaryBetResult"),
]


CurrentUserResult = Annotated[
    Union[User, InvalidToken, ExpiredToken],
    strawberry.union("CurrentUserResult"),
]


@strawberry.type
class AllTeamsSuccessful:
    teams: list[Team]


AllTeamsResult = Annotated[
    Union[AllTeamsSuccessful, InvalidToken, ExpiredToken],
    strawberry.union("AllTeamsResult"),
]


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


TeamByIdResult = Annotated[
    Union[Team, TeamByIdNotFound, InvalidToken, ExpiredToken],
    strawberry.union("TeamByIdResult"),
]

TeamByCodeResult = Annotated[
    Union[Team, TeamByCodeNotFound, InvalidToken, ExpiredToken],
    strawberry.union("TeamByCodeResult"),
]


@strawberry.type
class ScoreBetNotFound:
    id: strawberry.Private[UUID]

    @strawberry.field
    def message(self) -> str:
        return score_bet_not_found_message(self.id)


ScoreBetResult = Annotated[
    Union[ScoreBet, ScoreBetNotFound, InvalidToken, ExpiredToken],
    strawberry.union("ScoreBetResult"),
]


@strawberry.type
class BinaryBetNotFound:
    id: strawberry.Private[UUID]

    @strawberry.field
    def message(self) -> str:
        return binary_bet_not_found_message(self.id)


BinaryBetResult = Annotated[
    Union[
        BinaryBet,
        BinaryBetNotFound,
        InvalidToken,
        ExpiredToken,
    ],
    strawberry.union("BinaryBetResult"),
]


@strawberry.type
class Groups:
    groups: list[Group]


AllGroupsResult = Annotated[
    Union[Groups, InvalidToken, ExpiredToken],
    strawberry.union("AllGroupsResult"),
]


@strawberry.type
class GroupByCodeNotFound:
    code: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return group_not_found_message(self.code)


GroupByCodeResult = Annotated[
    Union[Group, GroupByCodeNotFound, InvalidToken, ExpiredToken],
    strawberry.union(
        "GroupByCodeResult",
    ),
]


@strawberry.type
class GroupByIdNotFound:
    id: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return group_not_found_message(self.id)


GroupByIdResult = Annotated[
    Union[Group, GroupByIdNotFound, InvalidToken, ExpiredToken],
    strawberry.union(
        "GroupByIdResult",
    ),
]


@strawberry.type
class Phases:
    phases: list[Phase]


AllPhasesResult = Annotated[
    Union[Phases, InvalidToken, ExpiredToken],
    strawberry.union("AllPhasesResult"),
]


@strawberry.type
class PhaseByCodeNotFound:
    code: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return phase_not_found_message(self.code)


PhaseByCodeResult = Annotated[
    Union[Phase, PhaseByCodeNotFound, InvalidToken, ExpiredToken],
    strawberry.union(
        "PhaseByCodeResult",
    ),
]


@strawberry.type
class PhaseByIdNotFound:
    id: strawberry.Private[UUID]

    @strawberry.field
    def message(self) -> str:
        return phase_not_found_message(self.id)


PhaseByIdResult = Annotated[
    Union[Phase, PhaseByIdNotFound, InvalidToken, ExpiredToken],
    strawberry.union("PhaseByIdResult"),
]


@strawberry.type
class ScoreBoard:
    users: list[UserWithoutSensitiveInfo]


ScoreBoardResult = Annotated[
    Union[ScoreBoard, InvalidToken, ExpiredToken],
    strawberry.union(
        "ScoreBoardResult",
    ),
]


@strawberry.type
class UserNameAlreadyExists:
    user_name: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return name_already_exists_message(self.user_name)


@strawberry.type
class UnsatisfiedPasswordRequirements:
    message: str


SignupResult = Annotated[
    Union[UserWithToken, UserNameAlreadyExists, UnsatisfiedPasswordRequirements],
    strawberry.union("SignupResult"),
]


@strawberry.type
class InvalidCredentials:
    message: str = INVALID_CREDENTIALS_MESSAGE


LoginResult = Annotated[Union[UserWithToken, InvalidCredentials], strawberry.union("LoginResult")]


@strawberry.type
class GroupRank:
    group_rank: list[GroupPosition]
    group: Group


GroupRankByCodeResult = Annotated[
    Union[GroupRank, GroupByCodeNotFound, InvalidToken, ExpiredToken],
    strawberry.union(
        "GroupRankByCodeResult",
    ),
]


GroupRankByIdResult = Annotated[
    Union[GroupRank, GroupByIdNotFound, InvalidToken, ExpiredToken],
    strawberry.union(
        "GroupRankByIdResult",
    ),
]


@strawberry.type
class UserNotFound:
    id: strawberry.Private[UUID]

    @strawberry.field
    def message(self) -> str:
        return user_not_found_message(self.id)


ModifyUserResult = Annotated[
    Union[
        UserWithoutSensitiveInfo,
        UserNotFound,
        InvalidToken,
        ExpiredToken,
        UnauthorizedAccessToAdminAPI,
    ],
    strawberry.union(
        "ModifyUserResult",
    ),
]
