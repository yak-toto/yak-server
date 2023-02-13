import uuid
from typing import Optional, Union

import strawberry

from .schema import (
    BinaryBet,
    Group,
    Phase,
    ScoreBet,
    Team,
    User,
    UserWithoutSensitiveInfo,
    UserWithToken,
)


@strawberry.type
class InvalidToken:
    message: str = "Invalid token. Cannot authentify."


@strawberry.type
class ExpiredToken:
    message: str = "Token is expired. Please reauthentify."


@strawberry.type
class UnauthorizedAccessToAdminAPI:
    message: str = "Unauthorized access to admin API"


@strawberry.type
class LockedScoreBetError:
    message: str = "Cannot modify score bet, resource is locked."


@strawberry.type
class ScoreBetNotFoundForUpdate:
    message: str = "Score bet not found. Cannot modify a ressource that does not exist."


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


ModifyScoreBetResult = Union[
    ScoreBet,
    ScoreBetNotFoundForUpdate,
    LockedScoreBetError,
    NewScoreNegative,
    InvalidToken,
    ExpiredToken,
]


@strawberry.type
class LockedBinaryBetError:
    message: str = "Cannot modify binary bet, resource is locked."


@strawberry.type
class BinaryBetNotFoundForUpdate:
    message: str = "Binary bet not found. Cannot modify a ressource that does not exist."


ModifyBinaryBetResult = Union[
    BinaryBet,
    BinaryBetNotFoundForUpdate,
    LockedBinaryBetError,
    InvalidToken,
    ExpiredToken,
]


CurrentUserResult = Union[User, InvalidToken, ExpiredToken]


@strawberry.type
class AllTeamsSuccessful:
    teams: list[Team]


AllTeamsResult = Union[AllTeamsSuccessful, InvalidToken, ExpiredToken]


@strawberry.type
class TeamByIdNotFound:
    id: strawberry.Private[uuid.UUID]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find team with id: {self.id}"


@strawberry.type
class TeamByCodeNotFound:
    code: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find team with code: {self.code}"


TeamByIdResult = Union[Team, TeamByIdNotFound, InvalidToken, ExpiredToken]
TeamByCodeResult = Union[Team, TeamByCodeNotFound, InvalidToken, ExpiredToken]


@strawberry.type
class TeamResponse:
    team: Optional[Team]
    errors: Optional[list[Union[InvalidToken, ExpiredToken]]]


@strawberry.type
class ScoreBetNotFound:
    id: strawberry.Private[uuid.UUID]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find score bet with id: {self.id}"


ScoreBetResult = Union[ScoreBet, ScoreBetNotFound, InvalidToken, ExpiredToken]


@strawberry.type
class BinaryBetNotFound:
    id: strawberry.Private[uuid.UUID]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find binary bet with id: {self.id}"


BinaryBetResult = Union[
    BinaryBet,
    BinaryBetNotFound,
    InvalidToken,
    ExpiredToken,
]


@strawberry.type
class Groups:
    groups: list[Group]


AllGroupsResult = Union[Groups, InvalidToken, ExpiredToken]


@strawberry.type
class GroupByCodeNotFound:
    code: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find group with code: {self.code}"


GroupByCodeResult = Union[Group, GroupByCodeNotFound, InvalidToken, ExpiredToken]


@strawberry.type
class GroupByIdNotFound:
    id: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find group with id: {self.id}"


GroupByIdResult = Union[Group, GroupByIdNotFound, InvalidToken, ExpiredToken]


@strawberry.type
class Phases:
    phases: list[Phase]


AllPhasesResult = Union[Phases, InvalidToken, ExpiredToken]


@strawberry.type
class PhaseByCodeNotFound:
    code: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find phase with code: {self.code}"


PhaseByCodeResult = Union[Phase, PhaseByCodeNotFound, InvalidToken, ExpiredToken]


@strawberry.type
class PhaseByIdNotFound:
    id: strawberry.Private[uuid.UUID]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find phase with id: {self.id}"


PhaseByIdResult = Union[Phase, PhaseByIdNotFound, InvalidToken, ExpiredToken]


@strawberry.type
class ScoreBoard:
    users: list[UserWithoutSensitiveInfo]


ScoreBoardResult = Union[ScoreBoard, InvalidToken, ExpiredToken]


@strawberry.type
class UserNameAlreadyExists:
    user_name: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return f"Name already exists: {self.user_name}"


SignupResult = Union[UserWithToken, UserNameAlreadyExists]


@strawberry.type
class InvalidCredentials:
    message: str = "Invalid credentials"


LoginResult = Union[UserWithToken, InvalidCredentials]


@strawberry.type
class UserNotFound:
    user_id: strawberry.Private[uuid.UUID]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find user with id: {self.user_id}"


LockUserResult = Union[User, UserNotFound, InvalidToken, ExpiredToken, UnauthorizedAccessToAdminAPI]


UserResult = Union[User, InvalidToken, ExpiredToken, UserNotFound, UnauthorizedAccessToAdminAPI]
