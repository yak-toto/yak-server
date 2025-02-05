from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from pydantic import computed_field
from sqlmodel import Field, Relationship, SQLModel, select

if TYPE_CHECKING:
    from sqlmodel import Session

ph = PasswordHasher()


class UserModel(SQLModel, table=True):
    __tablename__ = "user"
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    name: str = Field(max_length=100, unique=True)
    first_name: str = Field(max_length=100, nullable=False)
    last_name: str = Field(max_length=100, nullable=False)
    password: str = Field(max_length=100, nullable=False)

    number_match_guess: int = Field(ge=0, default=0)
    number_score_guess: int = Field(ge=0, default=0)
    number_qualified_teams_guess: int = Field(ge=0, default=0)
    number_first_qualified_guess: int = Field(ge=0, default=0)
    number_quarter_final_guess: int = Field(ge=0, default=0)
    number_semi_final_guess: int = Field(ge=0, default=0)
    number_final_guess: int = Field(ge=0, default=0)
    number_winner_guess: int = Field(ge=0, default=0)
    points: float = Field(ge=0, default=0)

    matches: list["MatchModel"] = Relationship(back_populates="user")

    def __init__(self, *, name: str, first_name: str, last_name: str, password: str) -> None:
        self.name = name
        self.first_name = first_name
        self.last_name = last_name
        self.password = ph.hash(password)

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @classmethod
    def authenticate(cls, session: "Session", name: str, password: str) -> "UserModel":
        user = session.exec(select(cls).where(cls.name == name)).first()

        is_correct_username = bool(user)

        try:
            if is_correct_username:
                ph.verify(user.password, password)
            else:
                # verify password with itself to avoid timing attack
                ph.verify(ph.hash(password), password)
            is_correct_password = True
        except VerificationError:
            is_correct_password = False

        return user if is_correct_username and is_correct_password else None

    def change_password(self, new_password: str) -> None:
        self.password = ph.hash(new_password)


class ScoreBetModel(SQLModel, table=True):
    __tablename__ = "score_bet"
    id: UUID = Field(primary_key=True, default_factory=uuid4)

    match_id: UUID = Field(foreign_key="match.id")
    match: "MatchModel" = Relationship(back_populates="score_bets")

    score1: Optional[int] = Field(ge=0)
    score2: Optional[int] = Field(ge=0)


class BinaryBetModel(SQLModel, table=True):
    __tablename__ = "binary_bet"
    id: UUID = Field(primary_key=True, default_factory=uuid4)

    match_id: UUID = Field(foreign_key="match.id", nullable=False)
    match: "MatchModel" = Relationship(back_populates="binary_bets")

    is_one_won: Optional[bool] = Field(default_factory=None)


class BetMapping(Enum):
    SCORE_BET = ScoreBetModel
    BINARY_BET = BinaryBetModel


class MatchReferenceModel(SQLModel, table=True):
    __tablename__ = "match_reference"
    id: UUID = Field(primary_key=True, default_factory=uuid4)

    group_id: UUID = Field(foreign_key="group.id")

    index: int

    team1_id: Optional[UUID] = Field(foreign_key="team.id")
    team2_id: Optional[UUID] = Field(foreign_key="team.id")

    bet_type_from_match: BetMapping


class MatchModel(SQLModel, table=True):
    __tablename__ = "match"
    id: UUID = Field(primary_key=True, default_factory=uuid4)

    group_id: UUID = Field(foreign_key="group.id")
    group: "GroupModel" = Relationship()

    index: int

    team1_id: Optional[UUID] = Field(foreign_key="team.id")
    team1: "TeamModel" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "MatchModel.team1_id"},
    )
    team2_id: Optional[UUID] = Field(foreign_key="team.id")
    team2: "TeamModel" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "MatchModel.team2_id"},
    )

    user_id: UUID = Field(foreign_key="user.id")
    user: UserModel = Relationship(back_populates="matches")

    score_bets: list[ScoreBetModel] = Relationship(back_populates="match", cascade_delete=True)
    binary_bets: list[BinaryBetModel] = Relationship(back_populates="match", cascade_delete=True)


class TeamModel(SQLModel, table=True):
    __tablename__ = "team"
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    code: str = Field(max_length=10, unique=True)
    description_fr: str = Field(max_length=100, unique=True)
    description_en: str = Field(max_length=100, unique=True)
    flag_url: str = Field(max_length=100)
    internal_flag_url: str = Field(max_length=300)


class GroupModel(SQLModel, table=True):
    __tablename__ = "group"
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    code: str = Field(max_length=10, unique=True)
    description_fr: str = Field(max_length=100, unique=True)
    description_en: str = Field(max_length=100, unique=True)
    index: int

    phase_id: UUID = Field(foreign_key="phase.id")
    phase: "PhaseModel" = Relationship()


class PhaseModel(SQLModel, table=True):
    __tablename__ = "phase"
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    code: str = Field(max_length=10, unique=True)
    description_fr: str = Field(max_length=100, unique=True)
    description_en: str = Field(max_length=100, unique=True)
    index: int


class GroupPositionModel(SQLModel, table=True):
    __tablename__ = "group_position"
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    won: int = Field(ge=0, nullable=False, default=0)
    drawn: int = Field(ge=0, nullable=False, default=0)
    lost: int = Field(ge=0, nullable=False, default=0)
    goals_for: int = Field(ge=0, nullable=False, default=0)
    goals_against: int = Field(ge=0, nullable=False, default=0)

    need_recomputation: bool = Field(nullable=False, default=False)

    user_id: UUID = Field(foreign_key="user.id")

    team_id: UUID = Field(foreign_key="team.id")
    team: TeamModel = Relationship()

    group_id: UUID = Field(foreign_key="group.id")

    @computed_field
    @property
    def played(self) -> int:
        return self.won + self.drawn + self.lost

    @computed_field
    @property
    def goals_difference(self) -> int:
        return self.goals_for - self.goals_against

    @computed_field
    @property
    def points(self) -> int:
        return self.won * 3 + self.drawn
