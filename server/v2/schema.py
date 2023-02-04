from typing import Optional, Union

import strawberry

from server.database.models import (
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
            BinaryBet.from_instance(instance=binary_bet) for binary_bet in self.instance.binary_bets
        ]

    @strawberry.field
    def score_bets(self) -> list["ScoreBet"]:
        return [ScoreBet.from_instance(instance=score_bet) for score_bet in self.instance.bets]

    @strawberry.field
    def phases(self) -> list["Phase"]:
        return [
            Phase.from_instance(instance=phase, user_id=self.instance.id)
            for phase in PhaseModel.query.all()
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
                .filter(
                    MatchModel.group_id == self.instance.id,
                )
            )
        ]

    @strawberry.field
    def binary_bets(self) -> list["BinaryBet"]:
        return [
            BinaryBet.from_instance(instance=binary_bet)
            for binary_bet in (
                BinaryBetModel.query.filter_by(user_id=self.user_id)
                .join(BinaryBetModel.match)
                .filter(
                    MatchModel.group_id == self.instance.id,
                )
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
            for group in self.instance.groups
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
class BetNotFound:
    message: str = "Score bet not found. Cannot modify a ressource that does not exist."


@strawberry.type
class ModifyScoreBetResponse:
    score_bet: Optional[ScoreBet]
    score_bet_errors: Optional[list[Union[LockedScoreBetError, BetNotFound]]]


@strawberry.type
class LockedBinaryBetError:
    message: str = "Cannot modify binary bet, resource is locked."


@strawberry.type
class BinaryBetNotFound:
    message: str = "Binary bet not found. Cannot modify a ressource that does not exist."


@strawberry.type
class ModifyBinaryBetResponse:
    binary_bet: Optional[BinaryBet]
    binary_bet_errors: Optional[list[Union[LockedBinaryBetError, BinaryBetNotFound]]]


@strawberry.type
class InvalidToken:
    message: str = "Invalid token. Cannot authentify."


@strawberry.type
class ExpiredToken:
    message: str = "Token is expired. Please reauthentify."


@strawberry.type
class GetUserResponse:
    user: Optional[User]
    errors: Optional[list[Union[InvalidToken, ExpiredToken]]]


@strawberry.type
class AllTeamsResponse:
    teams: Optional[list[Team]]
    errors: Optional[list[Union[InvalidToken, ExpiredToken]]]
