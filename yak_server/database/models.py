from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional, Union
from uuid import UUID, uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from pydantic import computed_field
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field, Relationship, SQLModel, select

if TYPE_CHECKING:
    from sqlmodel import Session

ph = PasswordHasher()


class UserModel(SQLModel, table=True):
    __tablename__ = "user"
    id: UUID = Field(primary_key=True, nullable=False, default_factory=uuid4)
    name: str = Field(max_length=100, unique=True, nullable=False)
    first_name: str = Field(max_length=100, nullable=False)
    last_name: str = Field(max_length=100, nullable=False)
    password: str = Field(max_length=100, nullable=False)
    number_match_guess: int = Field(
        default=0, nullable=False, sa_column_args=(CheckConstraint("number_match_guess>=0"),)
    )
    number_score_guess: int = Field(
        default=0, nullable=False, sa_column_args=(CheckConstraint("number_score_guess>=0"),)
    )
    number_qualified_teams_guess: int = Field(
        default=0,
        nullable=False,
        sa_column_args=(CheckConstraint("number_qualified_teams_guess>=0"),),
    )
    number_first_qualified_guess: int = Field(
        default=0,
        nullable=False,
        sa_column_args=(CheckConstraint("number_first_qualified_guess>=0"),),
    )
    number_quarter_final_guess: int = Field(
        default=0,
        nullable=False,
        sa_column_args=(CheckConstraint("number_quarter_final_guess>=0"),),
    )
    number_semi_final_guess: int = Field(
        default=0, nullable=False, sa_column_args=(CheckConstraint("number_semi_final_guess>=0"),)
    )
    number_final_guess: int = Field(
        default=0, nullable=False, sa_column_args=(CheckConstraint("number_final_guess>=0"),)
    )
    number_winner_guess: int = Field(
        default=0, nullable=False, sa_column_args=(CheckConstraint("number_winner_guess>=0"),)
    )

    points: float = Field(default=0, nullable=False, sa_column_args=(CheckConstraint("points>=0"),))

    refresh_tokens: list["RefreshTokenModel"] = Relationship(
        back_populates="user", cascade_delete=True, passive_deletes=True
    )

    matches: list["MatchModel"] = Relationship(
        back_populates="user",
        cascade_delete=True,
        passive_deletes=True,
    )

    def __init__(
        self,
        name: str,
        first_name: str,
        last_name: str,
        password: str,
    ) -> None:
        self.name = name
        self.first_name = first_name
        self.last_name = last_name
        self.password = ph.hash(password)

    @computed_field
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @classmethod
    def authenticate(cls, db: "Session", name: str, password: str) -> Optional["UserModel"]:
        user = db.exec(select(cls).where(cls.name == name)).first()

        try:
            if user is not None:
                ph.verify(user.password, password)
            else:
                # verify password with itself to avoid timing attack
                ph.verify(ph.hash(password), password)
            is_correct_password = True
        except VerificationError:
            is_correct_password = False

        return user if user and is_correct_password else None

    def change_password(self, new_password: str) -> None:
        self.password = ph.hash(new_password)


class RefreshTokenModel(SQLModel, table=True):
    __tablename__ = "refresh_token"
    id: UUID = Field(primary_key=True, nullable=False, default_factory=uuid4)
    user_id: UUID = Field(nullable=False, foreign_key="user.id", ondelete="CASCADE")
    user: UserModel = Relationship(back_populates="refresh_tokens")
    expiration: datetime = Field(nullable=False, sa_type=TIMESTAMP(timezone=True))


class ScoreBetModel(SQLModel, table=True):
    __tablename__ = "score_bet"

    id: UUID = Field(primary_key=True, nullable=False, default_factory=uuid4)

    match_id: UUID = Field(foreign_key="match.id", nullable=False)
    match: "MatchModel" = Relationship(back_populates="score_bets")

    score1: Optional[int] = Field(default=None, sa_column_args=(CheckConstraint("score1>=0"),))
    score2: Optional[int] = Field(default=None, sa_column_args=(CheckConstraint("score2>=0"),))

    def is_invalid(self) -> bool:
        return None in {self.score1, self.score2}

    def is_valid(self) -> bool:
        return not self.is_invalid()

    def is_1_win(self) -> bool:
        return self.score1 is not None and self.score2 is not None and self.score1 > self.score2

    def is_draw(self) -> bool:
        return self.score1 is not None and self.score2 is not None and self.score1 == self.score2

    def is_2_win(self) -> bool:
        return self.score1 is not None and self.score2 is not None and self.score1 < self.score2

    def is_same_results(self, other: "ScoreBetModel") -> bool:
        return (
            (self.is_1_win() and other.is_1_win())
            or (self.is_draw() and other.is_draw())
            or (self.is_2_win() and other.is_2_win())
        )

    def is_same_scores(self, other: "ScoreBetModel") -> bool:
        return (
            self.is_valid()
            and other.is_valid()
            and self.score1 == other.score1
            and self.score2 == other.score2
        )


class BinaryBetModel(SQLModel, table=True):
    __tablename__ = "binary_bet"
    id: UUID = Field(primary_key=True, nullable=False, default_factory=uuid4)

    match_id: UUID = Field(foreign_key="match.id", nullable=False)
    match: "MatchModel" = Relationship(back_populates="binary_bets")

    is_one_won: Optional[bool] = Field(default=None)

    def bet_from_is_one_won(self) -> Union[tuple[None, None], tuple[bool, bool]]:
        if self.is_one_won is None:
            return (None, None)

        return (self.is_one_won, not self.is_one_won)


class BetMapping(Enum):
    SCORE_BET = ScoreBetModel
    BINARY_BET = BinaryBetModel


class MatchReferenceModel(SQLModel, table=True):
    __tablename__ = "match_reference"
    id: UUID = Field(primary_key=True, nullable=False, default_factory=uuid4)

    group_id: UUID = Field(foreign_key="group.id", nullable=False)

    index: int = Field(nullable=False)

    team1_id: UUID = Field(foreign_key="team.id", nullable=True)
    team2_id: UUID = Field(foreign_key="team.id", nullable=True)

    bet_type_from_match: BetMapping = Field(nullable=False)

    __table_args__ = (UniqueConstraint("group_id", "index", name="uq_columns_group_id_index"),)


class MatchModel(SQLModel, table=True):
    __tablename__ = "match"
    id: UUID = Field(primary_key=True, nullable=False, default_factory=uuid4)

    group_id: UUID = Field(foreign_key="group.id", nullable=False)
    group: "GroupModel" = Relationship()

    index: int = Field(nullable=False)

    team1_id: Optional[UUID] = Field(foreign_key="team.id", nullable=True)
    team1: Optional["TeamModel"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "MatchModel.team1_id"}
    )

    team2_id: Optional[UUID] = Field(foreign_key="team.id", nullable=True)
    team2: Optional["TeamModel"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "MatchModel.team2_id"}
    )

    user_id: UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    user: UserModel = Relationship(back_populates="matches")

    score_bets: list[ScoreBetModel] = Relationship(
        back_populates="match",
        cascade_delete=True,
        passive_deletes=True,
    )
    binary_bets: list[BinaryBetModel] = Relationship(
        back_populates="match",
        cascade_delete=True,
        passive_deletes=True,
    )


class TeamModel(SQLModel, table=True):
    __tablename__ = "team"
    id: UUID = Field(primary_key=True, nullable=False, default_factory=uuid4)
    code: str = Field(max_length=10, unique=True, nullable=False)
    description_fr: str = Field(max_length=100, unique=True, nullable=False)
    description_en: str = Field(max_length=100, unique=True, nullable=False)
    flag_url: str = Field(max_length=100, nullable=False)
    internal_flag_url: str = Field(max_length=300, nullable=False)


class GroupModel(SQLModel, table=True):
    __tablename__ = "group"
    id: UUID = Field(primary_key=True, nullable=False, default_factory=uuid4)
    code: str = Field(max_length=1, unique=True, nullable=False)
    description_fr: str = Field(max_length=100, unique=True, nullable=False)
    description_en: str = Field(max_length=100, unique=True, nullable=False)
    index: int = Field(nullable=False)

    phase_id: UUID = Field(foreign_key="phase.id", nullable=False)
    phase: "PhaseModel" = Relationship()


class PhaseModel(SQLModel, table=True):
    __tablename__ = "phase"
    id: UUID = Field(primary_key=True, nullable=False, default_factory=uuid4)
    code: str = Field(max_length=10, unique=True, nullable=False)
    description_fr: str = Field(max_length=100, nullable=False)
    description_en: str = Field(max_length=100, nullable=False)
    index: int = Field(nullable=False)


class GroupPositionModel(SQLModel, table=True):
    __tablename__ = "group_position"
    id: UUID = Field(primary_key=True, nullable=False, default_factory=uuid4)
    won: int = Field(default=0, nullable=False, sa_column_args=(CheckConstraint("won>=0"),))
    drawn: int = Field(default=0, nullable=False, sa_column_args=(CheckConstraint("drawn>=0"),))
    lost: int = Field(default=0, nullable=False, sa_column_args=(CheckConstraint("lost>=0"),))
    goals_for: int = Field(
        default=0, nullable=False, sa_column_args=(CheckConstraint("goals_for>=0"),)
    )
    goals_against: int = Field(
        default=0, nullable=False, sa_column_args=(CheckConstraint("goals_against>=0"),)
    )

    need_recomputation: bool = Field(default=False, nullable=False)

    user_id: UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    user: UserModel = Relationship()

    team_id: UUID = Field(foreign_key="team.id", nullable=False)
    team: TeamModel = Relationship()

    group_id: UUID = Field(foreign_key="group.id", nullable=False)
    group: GroupModel = Relationship()

    @computed_field
    def played(self) -> int:
        return self.won + self.drawn + self.lost

    @computed_field
    def goals_difference(self) -> int:
        return self.goals_for - self.goals_against

    @computed_field
    def points(self) -> int:
        return self.won * 3 + self.drawn
