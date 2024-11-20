from typing import Optional
from uuid import UUID

import pendulum
import strawberry
from sqlalchemy import and_
from sqlalchemy.orm import Session

from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    GroupPositionModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    TeamModel,
    UserModel,
)
from yak_server.helpers.bet_locking import is_locked
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

    result: Result

    @strawberry.field
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @classmethod
    def from_instance(cls, instance: UserModel) -> "UserWithoutSensitiveInfo":
        return cls(
            instance=instance,
            first_name=instance.first_name,
            last_name=instance.last_name,
            result=Result.from_instance(instance),
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
            description=instance.description_fr,
            flag=Flag(url=instance.flag_url),
        )


@strawberry.type
class TeamWithScore(Team):
    score: Optional[int]

    @classmethod
    def from_instance(cls, instance: TeamModel, *, score: Optional[int]) -> "TeamWithScore":
        return cls(
            instance=instance,
            id=instance.id,
            code=instance.code,
            description=instance.description_fr,
            flag=Flag(url=instance.flag_url),
            score=score,
        )


@strawberry.type
class TeamWithVictory(Team):
    won: Optional[bool]

    @classmethod
    def from_instance(cls, instance: TeamModel, *, won: Optional[bool]) -> "TeamWithVictory":
        return cls(
            instance=instance,
            id=instance.id,
            code=instance.code,
            description=instance.description_fr,
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
            team=Team.from_instance(instance.team),
            played=instance.won + instance.drawn + instance.lost,
            won=instance.won,
            drawn=instance.drawn,
            lost=instance.lost,
            goals_for=instance.goals_for,
            goals_against=instance.goals_against,
        )


def send_group_position(group_rank: list[GroupPositionModel]) -> list[GroupPosition]:
    return sorted(
        [GroupPosition.from_instance(group_position) for group_position in group_rank],
        key=lambda team: (
            team.points(),
            team.goals_difference(),
            team.goals_for,
        ),
        reverse=True,
    )


@strawberry.type
class Group:
    db: strawberry.Private[Session]
    instance: strawberry.Private[GroupModel]
    user: strawberry.Private[UserModel]
    lock_datetime: strawberry.Private[pendulum.DateTime]

    id: UUID
    code: str
    description: str

    @strawberry.field
    def group_rank(self) -> list[GroupPosition]:
        group_rank = self.db.query(GroupPositionModel).filter_by(
            user_id=self.user.id,
            group_id=self.id,
        )

        if not any(group_position.need_recomputation for group_position in group_rank):
            return send_group_position(group_rank)

        score_bets = (
            self.db.query(ScoreBetModel)
            .join(ScoreBetModel.match)
            .filter(and_(MatchModel.user_id == self.user.id, MatchModel.group_id == self.id))
        )
        group_rank = compute_group_rank(group_rank, score_bets)
        self.db.commit()

        return send_group_position(group_rank)

    @strawberry.field
    def phase(self) -> "Phase":
        return Phase.from_instance(
            self.instance.phase,
            db=self.db,
            user=self.user,
            lock_datetime=self.lock_datetime,
        )

    @strawberry.field
    def score_bets(self) -> list["ScoreBet"]:
        return [
            ScoreBet.from_instance(score_bet, db=self.db, lock_datetime=self.lock_datetime)
            for score_bet in (
                self.db.query(ScoreBetModel)
                .join(ScoreBetModel.match)
                .filter_by(user_id=self.user.id)
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
            BinaryBet.from_instance(binary_bet, db=self.db, lock_datetime=self.lock_datetime)
            for binary_bet in (
                self.db.query(BinaryBetModel)
                .join(BinaryBetModel.match)
                .filter_by(user_id=self.user.id)
                .join(MatchModel.group)
                .filter(
                    MatchModel.group_id == self.instance.id,
                )
                .order_by(GroupModel.index, MatchModel.index)
            )
        ]

    @classmethod
    def from_instance(
        cls,
        instance: GroupModel,
        *,
        db: Session,
        user: UserModel,
        lock_datetime: pendulum.DateTime,
    ) -> "Group":
        return cls(
            db=db,
            instance=instance,
            user=user,
            lock_datetime=lock_datetime,
            id=instance.id,
            code=instance.code,
            description=instance.description_fr,
        )


@strawberry.type
class ScoreBet:
    instance: strawberry.Private[ScoreBetModel]

    id: UUID
    locked: bool
    group: Group
    team1: Optional[TeamWithScore]
    team2: Optional[TeamWithScore]

    @classmethod
    def from_instance(
        cls,
        instance: ScoreBetModel,
        *,
        db: "Session",
        lock_datetime: pendulum.DateTime,
    ) -> "ScoreBet":
        return cls(
            instance=instance,
            id=instance.id,
            locked=is_locked(instance.match.user.name, lock_datetime),
            group=Group.from_instance(
                instance.match.group,
                db=db,
                user=instance.match.user,
                lock_datetime=lock_datetime,
            ),
            team1=(
                TeamWithScore.from_instance(instance.match.team1, score=instance.score1)
                if instance.match.team1_id is not None
                else None
            ),
            team2=(
                TeamWithScore.from_instance(instance.match.team2, score=instance.score2)
                if instance.match.team2_id is not None
                else None
            ),
        )


@strawberry.type
class BinaryBet:
    instance: strawberry.Private[BinaryBetModel]

    id: UUID
    locked: bool
    group: Group
    team1: Optional[TeamWithVictory]
    team2: Optional[TeamWithVictory]

    @classmethod
    def from_instance(
        cls,
        instance: BinaryBetModel,
        *,
        db: "Session",
        lock_datetime: pendulum.DateTime,
    ) -> "BinaryBet":
        bet_results = instance.bet_from_is_one_won()

        return cls(
            instance=instance,
            id=instance.id,
            locked=is_locked(instance.match.user.name, lock_datetime),
            group=Group.from_instance(
                instance.match.group,
                db=db,
                user=instance.match.user,
                lock_datetime=lock_datetime,
            ),
            team1=(
                TeamWithVictory.from_instance(instance.match.team1, won=bet_results[0])
                if instance.match.team1_id is not None
                else None
            ),
            team2=(
                TeamWithVictory.from_instance(instance.match.team2, won=bet_results[1])
                if instance.match.team2_id is not None
                else None
            ),
        )


@strawberry.type
class Phase:
    db: strawberry.Private[Session]
    instance: strawberry.Private[PhaseModel]
    user: strawberry.Private[UserModel]
    lock_datetime: strawberry.Private[pendulum.DateTime]

    id: UUID
    code: str
    description: str

    @strawberry.field
    def groups(self) -> list[Group]:
        return [
            Group.from_instance(group, db=self.db, user=self.user, lock_datetime=self.lock_datetime)
            for group in self.db.query(GroupModel)
            .filter_by(phase_id=self.instance.id)
            .order_by(
                GroupModel.index,
            )
        ]

    @strawberry.field
    def binary_bets(self) -> list["BinaryBet"]:
        return [
            BinaryBet.from_instance(binary_bet, db=self.db, lock_datetime=self.lock_datetime)
            for binary_bet in self.db.query(BinaryBetModel)
            .join(BinaryBetModel.match)
            .filter_by(user_id=self.user.id)
            .join(MatchModel.group)
            .filter(
                GroupModel.phase_id == self.instance.id,
            )
            .order_by(GroupModel.index, MatchModel.index)
        ]

    @strawberry.field
    def score_bets(self) -> list["ScoreBet"]:
        return [
            ScoreBet.from_instance(score_bet, db=self.db, lock_datetime=self.lock_datetime)
            for score_bet in self.db.query(ScoreBetModel)
            .join(ScoreBetModel.match)
            .filter_by(user_id=self.user.id)
            .join(MatchModel.group)
            .filter(
                GroupModel.phase_id == self.instance.id,
            )
            .order_by(GroupModel.index, MatchModel.index)
        ]

    @classmethod
    def from_instance(
        cls,
        instance: PhaseModel,
        *,
        db: Session,
        user: UserModel,
        lock_datetime: pendulum.DateTime,
    ) -> "Phase":
        return cls(
            db=db,
            instance=instance,
            user=user,
            lock_datetime=lock_datetime,
            id=instance.id,
            code=instance.code,
            description=instance.description_fr,
        )


@strawberry.type
class User:
    instance: strawberry.Private[UserModel]
    db: strawberry.Private[Session]
    lock_datetime: strawberry.Private[pendulum.DateTime]

    id: UUID
    pseudo: str
    first_name: str
    last_name: str

    result: Result

    @strawberry.field
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @strawberry.field
    def binary_bets(self) -> list["BinaryBet"]:
        return [
            BinaryBet.from_instance(binary_bet, db=self.db, lock_datetime=self.lock_datetime)
            for binary_bet in self.db.query(BinaryBetModel)
            .join(BinaryBetModel.match)
            .filter_by(user_id=self.instance.id)
            .join(MatchModel.group)
            .order_by(GroupModel.index, MatchModel.index)
        ]

    @strawberry.field
    def score_bets(self) -> list["ScoreBet"]:
        return [
            ScoreBet.from_instance(score_bet, db=self.db, lock_datetime=self.lock_datetime)
            for score_bet in self.db.query(ScoreBetModel)
            .join(ScoreBetModel.match)
            .filter_by(user_id=self.instance.id)
            .join(MatchModel.group)
            .order_by(GroupModel.index, MatchModel.index)
        ]

    @strawberry.field
    def groups(self) -> list["Group"]:
        return [
            Group.from_instance(
                group,
                db=self.db,
                user=self.instance,
                lock_datetime=self.lock_datetime,
            )
            for group in self.db.query(GroupModel).order_by(GroupModel.index)
        ]

    @strawberry.field
    def phases(self) -> list["Phase"]:
        return [
            Phase.from_instance(
                phase,
                db=self.db,
                user=self.instance,
                lock_datetime=self.lock_datetime,
            )
            for phase in self.db.query(PhaseModel).order_by(PhaseModel.index)
        ]

    @classmethod
    def from_instance(
        cls,
        instance: UserModel,
        *,
        db: Session,
        lock_datetime: pendulum.DateTime,
    ) -> "User":
        return cls(
            instance=instance,
            db=db,
            lock_datetime=lock_datetime,
            id=instance.id,
            pseudo=instance.name,
            first_name=instance.first_name,
            last_name=instance.last_name,
            result=Result.from_instance(instance),
        )


@strawberry.type
class UserWithToken(User):
    token: str

    @classmethod
    def from_instance(
        cls,
        instance: UserModel,
        *,
        db: Session,
        lock_datetime: pendulum.DateTime,
        token: str,
    ) -> "UserWithToken":
        return cls(
            instance=instance,
            db=db,
            lock_datetime=lock_datetime,
            id=instance.id,
            pseudo=instance.name,
            first_name=instance.first_name,
            last_name=instance.last_name,
            result=Result.from_instance(instance),
            token=token,
        )


@strawberry.type
class PasswordRequirementsResult:
    minimum_length: int
    uppercase: bool
    lowercase: bool
    digit: bool
    no_space: bool
