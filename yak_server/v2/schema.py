from typing import Optional, Union

import strawberry

from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    TeamModel,
    UserModel,
)


@strawberry.type
class Result:
    instance: strawberry.Private[UserModel]

    number_match_guess: int
    number_score_guess: int
    number_qualified_teams_guess: int
    number_first_qualified_guess: int
    number_quarter_final_guess: int
    number_semi_final_guess: int
    number_final_guess: int
    number_winner_guess: int
    points: float

    @classmethod
    def from_instance(cls, instance: UserModel):
        return cls(
            instance=instance,
            number_match_guess=instance.number_match_guess,
            number_score_guess=instance.number_score_guess,
            number_qualified_teams_guess=instance.number_qualified_teams_guess,
            number_first_qualified_guess=instance.number_first_qualified_guess,
            number_quarter_final_guess=instance.number_quarter_final_guess,
            number_semi_final_guess=instance.number_semi_final_guess,
            number_final_guess=instance.number_final_guess,
            number_winner_guess=instance.number_winner_guess,
            points=instance.points,
        )


@strawberry.type
class UserWithoutSensitiveInfo:
    instance: strawberry.Private[UserModel]

    first_name: str
    last_name: str

    @strawberry.field
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    result: Result

    @classmethod
    def from_instance(cls, instance: UserModel):
        return cls(
            instance=instance,
            first_name=instance.first_name,
            last_name=instance.last_name,
            result=Result.from_instance(instance=instance),
        )


@strawberry.type
class User:
    instance: strawberry.Private[UserModel]

    pseudo: str
    first_name: str
    last_name: str

    @strawberry.field
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    result: Result

    @strawberry.field
    def binary_bets(self) -> list["BinaryBet"]:
        return [
            BinaryBet.from_instance(instance=binary_bet)
            for binary_bet in BinaryBetModel.query.filter_by(user_id=self.instance.id)
            .join(BinaryBetModel.match)
            .join(MatchModel.group)
            .order_by(GroupModel.index, MatchModel.index)
        ]

    @strawberry.field
    def score_bets(self) -> list["ScoreBet"]:
        return [
            ScoreBet.from_instance(instance=score_bet)
            for score_bet in ScoreBetModel.query.filter_by(user_id=self.instance.id)
            .join(ScoreBetModel.match)
            .join(MatchModel.group)
            .order_by(GroupModel.index, MatchModel.index)
        ]

    @strawberry.field
    def groups(self) -> list["Group"]:
        return [
            Group.from_instance(instance=group, user_id=self.instance.id)
            for group in GroupModel.query.order_by(GroupModel.index)
        ]

    @strawberry.field
    def phases(self) -> list["Phase"]:
        return [
            Phase.from_instance(instance=phase, user_id=self.instance.id)
            for phase in PhaseModel.query.order_by(PhaseModel.index)
        ]

    @classmethod
    def from_instance(cls, instance: UserModel):
        return cls(
            instance=instance,
            pseudo=instance.name,
            first_name=instance.first_name,
            last_name=instance.last_name,
            result=Result.from_instance(instance=instance),
        )


@strawberry.type
class UserWithToken(User):
    token: str

    @classmethod
    def from_instance(cls, instance: UserModel, token: str):
        return cls(
            instance=instance,
            pseudo=instance.name,
            first_name=instance.first_name,
            last_name=instance.last_name,
            result=Result.from_instance(instance=instance),
            token=token,
        )


@strawberry.type
class Team:
    instance: strawberry.Private[TeamModel]

    id: str
    code: str
    description: str

    @classmethod
    def from_instance(cls, instance: TeamModel):
        return cls(
            instance=instance,
            id=instance.id,
            code=instance.code,
            description=instance.description,
        )


@strawberry.type
class TeamWithScore(Team):
    score: Optional[int]

    @classmethod
    def from_instance(cls, instance: TeamModel, score: Optional[int]):
        return cls(
            instance=instance,
            id=instance.id,
            code=instance.code,
            description=instance.description,
            score=score,
        )


@strawberry.type
class TeamWithVictory(Team):
    won: Optional[bool]

    @classmethod
    def from_instance(cls, instance: TeamModel, won: Optional[bool]):
        return cls(
            instance=instance,
            id=instance.id,
            code=instance.code,
            description=instance.description,
            won=won,
        )


@strawberry.type
class Group:
    instance: strawberry.Private[GroupModel]
    user_id: strawberry.Private[str]

    id: str
    code: str
    description: str

    @strawberry.field
    def phase(self) -> "Phase":
        return Phase.from_instance(instance=self.instance.phase, user_id=self.user_id)

    @strawberry.field
    def score_bets(self) -> list["ScoreBet"]:
        return [
            ScoreBet.from_instance(instance=score_bet)
            for score_bet in (
                ScoreBetModel.query.filter_by(user_id=self.user_id)
                .join(ScoreBetModel.match)
                .join(MatchModel.group)
                .filter(
                    MatchModel.group_id == self.instance.id,
                )
                .order_by(GroupModel.index, MatchModel.index)
            )
        ]

    @strawberry.field
    def binary_bets(self) -> list["BinaryBet"]:
        return [
            BinaryBet.from_instance(instance=binary_bet)
            for binary_bet in (
                BinaryBetModel.query.filter_by(user_id=self.user_id)
                .join(BinaryBetModel.match)
                .join(MatchModel.group)
                .filter(
                    MatchModel.group_id == self.instance.id,
                )
                .order_by(GroupModel.index, MatchModel.index)
            )
        ]

    @classmethod
    def from_instance(cls, instance: GroupModel, user_id: str):
        return cls(
            instance=instance,
            user_id=user_id,
            id=instance.id,
            code=instance.code,
            description=instance.description,
        )


@strawberry.type
class Phase:
    instance: strawberry.Private[PhaseModel]
    user_id: strawberry.Private[str]

    id: str
    code: str
    description: str

    @strawberry.field
    def groups(self) -> list[Group]:
        return [
            Group.from_instance(instance=group, user_id=self.user_id)
            for group in GroupModel.query.filter_by(phase_id=self.instance.id).order_by(
                GroupModel.index,
            )
        ]

    @strawberry.field
    def binary_bets(self) -> list["BinaryBet"]:
        return [
            BinaryBet.from_instance(instance=binary_bet)
            for binary_bet in BinaryBetModel.query.filter_by(user_id=self.user_id)
            .join(BinaryBetModel.match)
            .join(MatchModel.group)
            .filter(
                GroupModel.phase_id == self.instance.id,
            )
            .order_by(GroupModel.index, MatchModel.index)
        ]

    @strawberry.field
    def score_bets(self) -> list["ScoreBet"]:
        return [
            ScoreBet.from_instance(instance=score_bet)
            for score_bet in ScoreBetModel.query.filter_by(user_id=self.user_id)
            .join(ScoreBetModel.match)
            .join(MatchModel.group)
            .filter(
                GroupModel.phase_id == self.instance.id,
            )
            .order_by(GroupModel.index, MatchModel.index)
        ]

    @classmethod
    def from_instance(cls, instance: PhaseModel, user_id: str):
        return cls(
            instance=instance,
            user_id=user_id,
            id=instance.id,
            code=instance.code,
            description=instance.description,
        )


@strawberry.type
class ScoreBet:
    instance: strawberry.Private[ScoreBetModel]

    id: str
    match_id: str
    index: int
    locked: bool
    group: Group
    team1: TeamWithScore
    team2: TeamWithScore

    @classmethod
    def from_instance(cls, instance: ScoreBetModel):
        return cls(
            instance=instance,
            id=instance.id,
            match_id=instance.match_id,
            index=instance.match.index,
            locked=instance.locked,
            group=Group.from_instance(
                instance=instance.match.group,
                user_id=instance.user_id,
            ),
            team1=TeamWithScore.from_instance(
                instance=instance.match.team1,
                score=instance.score1,
            ),
            team2=TeamWithScore.from_instance(
                instance=instance.match.team2,
                score=instance.score2,
            ),
        )


@strawberry.type
class BinaryBet:
    instance: strawberry.Private[BinaryBetModel]

    id: str
    match_id: str
    index: int
    locked: bool
    group: Group
    team1: TeamWithVictory
    team2: TeamWithVictory

    @classmethod
    def from_instance(cls, instance: BinaryBetModel):
        bet_results = instance.bet_from_is_one_won()

        return cls(
            instance=instance,
            id=instance.id,
            match_id=instance.match_id,
            index=instance.match.index,
            locked=instance.locked,
            group=Group.from_instance(
                instance=instance.match.group,
                user_id=instance.user_id,
            ),
            team1=TeamWithVictory.from_instance(
                instance=instance.match.team1,
                won=bet_results[0],
            ),
            team2=TeamWithVictory.from_instance(
                instance=instance.match.team2,
                won=bet_results[1],
            ),
        )


@strawberry.type
class LockUserResponse:
    binary_bets: list[BinaryBet]
    score_bets: list[ScoreBet]


@strawberry.type
class LockedScoreBetError:
    message: str = "Cannot modify score bet, resource is locked."


@strawberry.type
class ScoreBetNotFoundForUpdate:
    message: str = "Score bet not found. Cannot modify a ressource that does not exist."


@strawberry.type
class ModifyScoreBetResponse:
    score_bet: Optional[ScoreBet]
    score_bet_errors: Optional[list[Union[LockedScoreBetError, ScoreBetNotFoundForUpdate]]]


@strawberry.type
class LockedBinaryBetError:
    message: str = "Cannot modify binary bet, resource is locked."


@strawberry.type
class BinaryBetNotFoundForUpdate:
    message: str = "Binary bet not found. Cannot modify a ressource that does not exist."


@strawberry.type
class ModifyBinaryBetResponse:
    binary_bet: Optional[BinaryBet]
    binary_bet_errors: Optional[list[Union[LockedBinaryBetError, BinaryBetNotFoundForUpdate]]]


@strawberry.type
class InvalidToken:
    message: str = "Invalid token. Cannot authentify."


@strawberry.type
class ExpiredToken:
    message: str = "Token is expired. Please reauthentify."


UserResult = Union[User, InvalidToken, ExpiredToken]


@strawberry.type
class AllTeamsSuccessful:
    teams: list[Team]


AllTeamsResult = Union[AllTeamsSuccessful, InvalidToken, ExpiredToken]


@strawberry.type
class TeamByIdNotFound:
    id: strawberry.Private[str]

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
    id: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find score bet with id: {self.id}"


ScoreBetResult = Union[ScoreBet, ScoreBetNotFound, InvalidToken, ExpiredToken]


@strawberry.type
class BinaryBetNotFound:
    id: strawberry.Private[str]

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
    id: strawberry.Private[str]

    @strawberry.field
    def message(self) -> str:
        return f"Cannot find phase with id: {self.id}"


PhaseByIdResult = Union[Phase, PhaseByIdNotFound, InvalidToken, ExpiredToken]


@strawberry.type
class ScoreBoard:
    users: list[UserWithoutSensitiveInfo]


ScoreBoardResult = Union[ScoreBoard, InvalidToken, ExpiredToken]
