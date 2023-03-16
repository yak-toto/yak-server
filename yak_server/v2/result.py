from uuid import UUID

import strawberry

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
    message: str = "Cannot modify binary bet, resource is locked."


@strawberry.type
class BinaryBetNotFoundForUpdate:
    message: str = "Binary bet not found. Cannot modify a ressource that does not exist."


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
    teams: list[Team]


AllTeamsResult = strawberry.union(
    "AllTeamsResult",
    types=(AllTeamsSuccessful, InvalidToken, ExpiredToken),
)


@strawberry.type
class TeamByIdNotFound:
    id: strawberry.Private[UUID]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find team with id: {self.id}"


@strawberry.type
class TeamByCodeNotFound:
    code: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find team with code: {self.code}"


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
        return f"Cannot find score bet with id: {self.id}"


ScoreBetResult = strawberry.union(
    "ScoreBetResult",
    types=(ScoreBet, ScoreBetNotFound, InvalidToken, ExpiredToken),
)


@strawberry.type
class BinaryBetNotFound:
    id: strawberry.Private[UUID]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find binary bet with id: {self.id}"


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
    groups: list[Group]


AllGroupsResult = strawberry.union("AllGroupsResult", types=(Groups, InvalidToken, ExpiredToken))


@strawberry.type
class GroupByCodeNotFound:
    code: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find group with code: {self.code}"


GroupByCodeResult = strawberry.union(
    "GroupByCodeResult",
    types=(Group, GroupByCodeNotFound, InvalidToken, ExpiredToken),
)


@strawberry.type
class GroupByIdNotFound:
    id: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find group with id: {self.id}"


GroupByIdResult = strawberry.union(
    "GroupByIdResult",
    types=(Group, GroupByIdNotFound, InvalidToken, ExpiredToken),
)


@strawberry.type
class Phases:
    phases: list[Phase]


AllPhasesResult = strawberry.union("AllPhasesResult", types=(Phases, InvalidToken, ExpiredToken))


@strawberry.type
class PhaseByCodeNotFound:
    code: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find phase with code: {self.code}"


PhaseByCodeResult = strawberry.union(
    "PhaseByCodeResult",
    types=(Phase, PhaseByCodeNotFound, InvalidToken, ExpiredToken),
)


@strawberry.type
class PhaseByIdNotFound:
    id: strawberry.Private[UUID]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find phase with id: {self.id}"


PhaseByIdResult = strawberry.union(
    "PhaseByIdResult",
    types=(Phase, PhaseByIdNotFound, InvalidToken, ExpiredToken),
)


@strawberry.type
class ScoreBoard:
    users: list[UserWithoutSensitiveInfo]


ScoreBoardResult = strawberry.union(
    "ScoreBoardResult",
    types=(ScoreBoard, InvalidToken, ExpiredToken),
)


@strawberry.type
class UserNameAlreadyExists:
    user_name: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return f"Name already exists: {self.user_name}"


SignupResult = strawberry.union("SignupResult", types=(UserWithToken, UserNameAlreadyExists))


@strawberry.type
class InvalidCredentials:
    message: str = "Invalid credentials"


LoginResult = strawberry.union("LoginResult", types=(UserWithToken, InvalidCredentials))


@strawberry.type
class GroupRank:
    group_rank: list[GroupPosition]
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
        return f"User not found with id: {self.id}"


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
