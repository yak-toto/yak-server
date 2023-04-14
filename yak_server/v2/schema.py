from typing import List, Optional
from uuid import UUID

import strawberry

from yak_server import db
from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    GroupPositionModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    TeamModel,
    UserModel,
    is_locked,
)
from yak_server.helpers.group_position import compute_group_rank


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
    def from_instance(cls, instance: UserModel) -> "Result":
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
    def from_instance(cls, instance: UserModel) -> "UserWithoutSensitiveInfo":
        return cls(
            instance=instance,
            first_name=instance.first_name,
            last_name=instance.last_name,
            result=Result.from_instance(instance=instance),
        )


@strawberry.type
class User:
    instance: strawberry.Private[UserModel]

    id: UUID
    pseudo: str
    first_name: str
    last_name: str

    @strawberry.field
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    result: Result

    @strawberry.field
    def binary_bets(self) -> List["BinaryBet"]:
        return [
            BinaryBet.from_instance(instance=binary_bet)
            for binary_bet in BinaryBetModel.query.filter_by(user_id=self.instance.id)
            .join(BinaryBetModel.match)
            .join(MatchModel.group)
            .order_by(GroupModel.index, MatchModel.index)
        ]

    @strawberry.field
    def score_bets(self) -> List["ScoreBet"]:
        return [
            ScoreBet.from_instance(instance=score_bet)
            for score_bet in ScoreBetModel.query.filter_by(user_id=self.instance.id)
            .join(ScoreBetModel.match)
            .join(MatchModel.group)
            .order_by(GroupModel.index, MatchModel.index)
        ]

    @strawberry.field
    def groups(self) -> List["Group"]:
        return [
            Group.from_instance(instance=group, user_id=self.instance.id)
            for group in GroupModel.query.order_by(GroupModel.index)
        ]

    @strawberry.field
    def phases(self) -> List["Phase"]:
        return [
            Phase.from_instance(instance=phase, user_id=self.instance.id)
            for phase in PhaseModel.query.order_by(PhaseModel.index)
        ]

    @classmethod
    def from_instance(cls, instance: UserModel) -> "User":
        return cls(
            instance=instance,
            id=instance.id,
            pseudo=instance.name,
            first_name=instance.first_name,
            last_name=instance.last_name,
            result=Result.from_instance(instance=instance),
        )


@strawberry.type
class UserWithToken(User):
    token: str

    @classmethod
    def from_instance(cls, instance: UserModel, token: str) -> "UserWithToken":
        return cls(
            instance=instance,
            id=instance.id,
            pseudo=instance.name,
            first_name=instance.first_name,
            last_name=instance.last_name,
            result=Result.from_instance(instance=instance),
            token=token,
        )


@strawberry.type
class Flag:
    url: str


@strawberry.type
class Team:
    instance: strawberry.Private[TeamModel]

    id: UUID
    code: str
    description: str
    flag: Flag

    @classmethod
    def from_instance(cls, instance: TeamModel) -> "Team":
        return cls(
            instance=instance,
            id=instance.id,
            code=instance.code,
            description=instance.description,
            flag=Flag(url=instance.flag_url),
        )


@strawberry.type
class TeamWithScore(Team):
    score: Optional[int]

    @classmethod
    def from_instance(cls, instance: TeamModel, score: Optional[int]) -> "TeamWithScore":
        return cls(
            instance=instance,
            id=instance.id,
            code=instance.code,
            description=instance.description,
            flag=Flag(url=instance.flag_url),
            score=score,
        )


@strawberry.type
class TeamWithVictory(Team):
    won: Optional[bool]

    @classmethod
    def from_instance(cls, instance: TeamModel, won: Optional[bool]) -> "TeamWithVictory":
        return cls(
            instance=instance,
            id=instance.id,
            code=instance.code,
            description=instance.description,
            flag=Flag(url=instance.flag_url),
            won=won,
        )


@strawberry.type
class GroupPosition:
    instance: strawberry.Private[GroupPositionModel]

    team: Team
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int

    @strawberry.field
    def goals_difference(self) -> int:
        return self.goals_for - self.goals_against

    @strawberry.field
    def points(self) -> int:
        return self.won * 3 + self.drawn

    @classmethod
    def from_instance(cls, instance: GroupPositionModel) -> "GroupPosition":
        return cls(
            instance=instance,
            team=Team.from_instance(instance=instance.team),
            played=instance.won + instance.drawn + instance.lost,
            won=instance.won,
            drawn=instance.drawn,
            lost=instance.lost,
            goals_for=instance.goals_for,
            goals_against=instance.goals_against,
        )


def send_group_position(group_rank: List[GroupPositionModel]) -> List[GroupPosition]:
    return sorted(
        [GroupPosition.from_instance(instance=group_position) for group_position in group_rank],
        key=lambda team: (
            team.points(),
            team.goals_difference(),
            team.goals_for,
        ),
        reverse=True,
    )


@strawberry.type
class Group:
    instance: strawberry.Private[GroupModel]
    user_id: strawberry.Private[str]

    id: UUID
    code: str
    description: str

    @strawberry.field
    def group_rank(self) -> List[GroupPosition]:
        group_rank = GroupPositionModel.query.filter_by(user_id=self.user_id, group_id=self.id)

        if not any(group_position.need_recomputation for group_position in group_rank):
            return send_group_position(group_rank)

        user = UserModel.query.filter_by(id=self.user_id).first()

        score_bets = user.score_bets.filter(MatchModel.group_id == self.id).join(
            ScoreBetModel.match,
        )
        group_rank = compute_group_rank(group_rank, score_bets)
        db.session.commit()

        return send_group_position(group_rank)

    @strawberry.field
    def phase(self) -> "Phase":
        return Phase.from_instance(instance=self.instance.phase, user_id=self.user_id)

    @strawberry.field
    def score_bets(self) -> List["ScoreBet"]:
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
    def binary_bets(self) -> List["BinaryBet"]:
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
    def from_instance(cls, instance: GroupModel, user_id: str) -> "Group":
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

    id: UUID
    code: str
    description: str

    @strawberry.field
    def groups(self) -> List[Group]:
        return [
            Group.from_instance(instance=group, user_id=self.user_id)
            for group in GroupModel.query.filter_by(phase_id=self.instance.id).order_by(
                GroupModel.index,
            )
        ]

    @strawberry.field
    def binary_bets(self) -> List["BinaryBet"]:
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
    def score_bets(self) -> List["ScoreBet"]:
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
    def from_instance(cls, instance: PhaseModel, user_id: str) -> "Phase":
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

    id: UUID
    index: int
    locked: bool
    group: Group
    team1: Optional[TeamWithScore]
    team2: Optional[TeamWithScore]

    @classmethod
    def from_instance(cls, instance: ScoreBetModel) -> "ScoreBet":
        return cls(
            instance=instance,
            id=instance.id,
            index=instance.match.index,
            locked=is_locked(instance.user.name),
            group=Group.from_instance(
                instance=instance.match.group,
                user_id=instance.user_id,
            ),
            team1=TeamWithScore.from_instance(
                instance=instance.match.team1,
                score=instance.score1,
            )
            if instance.match.team1
            else None,
            team2=TeamWithScore.from_instance(
                instance=instance.match.team2,
                score=instance.score2,
            )
            if instance.match.team2
            else None,
        )


@strawberry.type
class BinaryBet:
    instance: strawberry.Private[BinaryBetModel]

    id: UUID
    index: int
    locked: bool
    group: Group
    team1: Optional[TeamWithVictory]
    team2: Optional[TeamWithVictory]

    @classmethod
    def from_instance(cls, instance: BinaryBetModel) -> "BinaryBet":
        bet_results = instance.bet_from_is_one_won()

        return cls(
            instance=instance,
            id=instance.id,
            index=instance.match.index,
            locked=is_locked(instance.user.name),
            group=Group.from_instance(
                instance=instance.match.group,
                user_id=instance.user_id,
            ),
            team1=TeamWithVictory.from_instance(
                instance=instance.match.team1,
                won=bet_results[0],
            )
            if instance.match.team1
            else None,
            team2=TeamWithVictory.from_instance(
                instance=instance.match.team2,
                won=bet_results[1],
            )
            if instance.match.team2
            else None,
        )
