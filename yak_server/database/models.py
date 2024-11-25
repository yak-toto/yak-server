from enum import Enum
from typing import TYPE_CHECKING
from uuid import uuid4

import sqlalchemy as sa
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from sqlalchemy import CheckConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from . import Base

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

ph = PasswordHasher()


class UserModel(Base):
    __tablename__ = "user"
    id = sa.Column(UUIDType(binary=False), primary_key=True, nullable=False, default=uuid4)
    name = sa.Column(sa.String(100), unique=True, nullable=False)
    first_name = sa.Column(sa.String(100), nullable=False)
    last_name = sa.Column(sa.String(100), nullable=False)

    password = sa.Column(sa.String(100), nullable=False)
    number_match_guess = sa.Column(
        sa.Integer,
        CheckConstraint("number_match_guess>=0"),
        nullable=False,
        default=0,
    )
    number_score_guess = sa.Column(
        sa.Integer,
        CheckConstraint("number_score_guess>=0"),
        nullable=False,
        default=0,
    )
    number_qualified_teams_guess = sa.Column(
        sa.Integer,
        CheckConstraint("number_qualified_teams_guess>=0"),
        nullable=False,
        default=0,
    )
    number_first_qualified_guess = sa.Column(
        sa.Integer,
        CheckConstraint("number_first_qualified_guess>=0"),
        nullable=False,
        default=0,
    )
    number_quarter_final_guess = sa.Column(
        sa.Integer,
        CheckConstraint("number_quarter_final_guess>=0"),
        nullable=False,
        default=0,
    )
    number_semi_final_guess = sa.Column(
        sa.Integer,
        CheckConstraint("number_semi_final_guess>=0"),
        nullable=False,
        default=0,
    )
    number_final_guess = sa.Column(
        sa.Integer,
        CheckConstraint("number_final_guess>=0"),
        nullable=False,
        default=0,
    )
    number_winner_guess = sa.Column(
        sa.Integer,
        CheckConstraint("number_winner_guess>=0"),
        nullable=False,
        default=0,
    )
    points = sa.Column(
        sa.Float,
        CheckConstraint("points>=0"),
        nullable=False,
        default=0,
    )

    matches = relationship(
        "MatchModel",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete",
        passive_deletes=True,
    )

    def __init__(self, name: str, first_name: str, last_name: str, password: str) -> None:
        self.name = name
        self.first_name = first_name
        self.last_name = last_name
        self.password = ph.hash(password)

    @hybrid_property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @classmethod
    def authenticate(cls, db: "Session", name: str, password: str) -> "UserModel":
        user = db.query(cls).filter_by(name=name).first()

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


class ScoreBetModel(Base):
    __tablename__ = "score_bet"
    id = sa.Column(UUIDType(binary=False), primary_key=True, nullable=False, default=uuid4)

    match_id = sa.Column(
        UUIDType(binary=False), sa.ForeignKey("match.id", ondelete="CASCADE"), nullable=False
    )
    match = relationship("MatchModel", back_populates="score_bets")

    score1 = sa.Column(sa.Integer, CheckConstraint("score1>=0"), default=None)
    score2 = sa.Column(sa.Integer, CheckConstraint("score2>=0"), default=None)

    def is_invalid(self) -> bool:
        return None in {self.score1, self.score2}

    def is_valid(self) -> bool:
        return not self.is_invalid()

    def is_1_win(self) -> bool:
        return self.is_valid() and self.score1 > self.score2

    def is_draw(self) -> bool:
        return self.is_valid() and self.score1 == self.score2

    def is_2_win(self) -> bool:
        return self.is_valid() and self.score1 < self.score2

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


class BinaryBetModel(Base):
    __tablename__ = "binary_bet"
    id = sa.Column(UUIDType(binary=False), primary_key=True, nullable=False, default=uuid4)

    match_id = sa.Column(
        UUIDType(binary=False), sa.ForeignKey("match.id", ondelete="CASCADE"), nullable=False
    )
    match = relationship("MatchModel", back_populates="binary_bets")

    is_one_won = sa.Column(sa.Boolean, default=None)

    def bet_from_is_one_won(self) -> tuple:
        if self.is_one_won is None:
            return (None, None)

        return (self.is_one_won, not self.is_one_won)


class BetMapping(Enum):
    SCORE_BET = ScoreBetModel
    BINARY_BET = BinaryBetModel


class MatchReferenceModel(Base):
    __tablename__ = "match_reference"
    id = sa.Column(UUIDType(binary=False), primary_key=True, nullable=False, default=uuid4)

    group_id = sa.Column(UUIDType(binary=False), sa.ForeignKey("group.id"), nullable=False)

    index = sa.Column(sa.Integer, nullable=False)

    team1_id = sa.Column(UUIDType(binary=False), sa.ForeignKey("team.id"), nullable=True)
    team2_id = sa.Column(UUIDType(binary=False), sa.ForeignKey("team.id"), nullable=True)

    bet_type_from_match = sa.Column(SqlEnum(BetMapping), nullable=False)


class MatchModel(Base):
    __tablename__ = "match"
    id = sa.Column(UUIDType(binary=False), primary_key=True, nullable=False, default=uuid4)

    group_id = sa.Column(UUIDType(binary=False), sa.ForeignKey("group.id"), nullable=False)
    group = relationship("GroupModel", foreign_keys=group_id, backref="matches")

    index = sa.Column(sa.Integer, nullable=False)

    team1_id = sa.Column(UUIDType(binary=False), sa.ForeignKey("team.id"), nullable=True)
    team1 = relationship("TeamModel", foreign_keys=team1_id)

    team2_id = sa.Column(UUIDType(binary=False), sa.ForeignKey("team.id"), nullable=True)
    team2 = relationship("TeamModel", foreign_keys=team2_id)

    user_id = sa.Column(
        UUIDType(binary=False), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    user = relationship("UserModel", foreign_keys=user_id)

    score_bets = relationship(
        "ScoreBetModel",
        back_populates="match",
        lazy="dynamic",
        cascade="all, delete",
        passive_deletes=True,
    )
    binary_bets = relationship(
        "BinaryBetModel",
        back_populates="match",
        lazy="dynamic",
        cascade="all, delete",
        passive_deletes=True,
    )


class TeamModel(Base):
    __tablename__ = "team"
    id = sa.Column(UUIDType(binary=False), primary_key=True, nullable=False, default=uuid4)
    code = sa.Column(sa.String(10), unique=True, nullable=False)
    description_fr = sa.Column(sa.String(100), unique=True, nullable=False)
    description_en = sa.Column(sa.String(100), unique=True, nullable=False)
    flag_url = sa.Column(sa.String(100), nullable=False)
    internal_flag_url = sa.Column(sa.String(300), nullable=False)


class GroupModel(Base):
    __tablename__ = "group"
    id = sa.Column(UUIDType(binary=False), primary_key=True, nullable=False, default=uuid4)
    code = sa.Column(sa.String(1), primary_key=True, unique=True, nullable=False)
    description_fr = sa.Column(sa.String(100), unique=True, nullable=False)
    description_en = sa.Column(sa.String(100), unique=True, nullable=False)
    index = sa.Column(sa.Integer, nullable=False)

    phase_id = sa.Column(UUIDType(binary=False), sa.ForeignKey("phase.id"), nullable=False)
    phase = relationship("PhaseModel", backref="groups")


class PhaseModel(Base):
    __tablename__ = "phase"
    id = sa.Column(UUIDType(binary=False), primary_key=True, nullable=False, default=uuid4)
    code = sa.Column(sa.String(10), primary_key=True, unique=True, nullable=False)
    description_fr = sa.Column(sa.String(100), nullable=False)
    description_en = sa.Column(sa.String(100), nullable=False)
    index = sa.Column(sa.Integer, nullable=False)


class GroupPositionModel(Base):
    __tablename__ = "group_position"
    id = sa.Column(UUIDType(binary=False), primary_key=True, nullable=False, default=uuid4)
    won = sa.Column(sa.Integer, CheckConstraint("won>=0"), nullable=False, default=0)
    drawn = sa.Column(sa.Integer, CheckConstraint("drawn>=0"), nullable=False, default=0)
    lost = sa.Column(sa.Integer, CheckConstraint("lost>=0"), nullable=False, default=0)
    goals_for = sa.Column(sa.Integer, CheckConstraint("goals_for>=0"), nullable=False, default=0)
    goals_against = sa.Column(
        sa.Integer,
        CheckConstraint("goals_against>=0"),
        nullable=False,
        default=0,
    )

    need_recomputation = sa.Column(sa.Boolean, nullable=False, default=False)

    user_id = sa.Column(
        UUIDType(binary=False),
        sa.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )

    team_id = sa.Column(
        UUIDType(binary=False),
        sa.ForeignKey("team.id"),
        nullable=False,
    )
    team = relationship("TeamModel")

    group_id = sa.Column(
        UUIDType(binary=False),
        sa.ForeignKey("group.id"),
        nullable=False,
    )

    @hybrid_property
    def played(self) -> int:
        return self.won + self.drawn + self.lost

    @hybrid_property
    def goals_difference(self) -> int:
        return self.goals_for - self.goals_against

    @hybrid_property
    def points(self) -> int:
        return self.won * 3 + self.drawn
