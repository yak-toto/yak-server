import contextlib
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

import sqlalchemy as sa
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID as DB_UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

ph = PasswordHasher()


class Base(DeclarativeBase):
    pass


class Role(Enum):
    USER = "user"
    ADMIN = "admin"


class UserModel(Base):
    __tablename__ = "user"
    id: Mapped[UUID] = mapped_column(DB_UUID(), primary_key=True, nullable=False, default=uuid4)
    name: Mapped[str] = mapped_column(sa.String(100), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    password: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    role: Mapped[Role] = mapped_column(SqlEnum(Role), nullable=False)
    number_match_guess: Mapped[int] = mapped_column(
        sa.Integer,
        CheckConstraint("number_match_guess>=0"),
        nullable=False,
        default=0,
    )
    number_score_guess: Mapped[int] = mapped_column(
        sa.Integer,
        CheckConstraint("number_score_guess>=0"),
        nullable=False,
        default=0,
    )
    number_qualified_teams_guess: Mapped[int] = mapped_column(
        sa.Integer,
        CheckConstraint("number_qualified_teams_guess>=0"),
        nullable=False,
        default=0,
    )
    number_first_qualified_guess: Mapped[int] = mapped_column(
        sa.Integer,
        CheckConstraint("number_first_qualified_guess>=0"),
        nullable=False,
        default=0,
    )
    number_quarter_final_guess: Mapped[int] = mapped_column(
        sa.Integer,
        CheckConstraint("number_quarter_final_guess>=0"),
        nullable=False,
        default=0,
    )
    number_semi_final_guess: Mapped[int] = mapped_column(
        sa.Integer,
        CheckConstraint("number_semi_final_guess>=0"),
        nullable=False,
        default=0,
    )
    number_final_guess: Mapped[int] = mapped_column(
        sa.Integer,
        CheckConstraint("number_final_guess>=0"),
        nullable=False,
        default=0,
    )
    number_winner_guess: Mapped[int] = mapped_column(
        sa.Integer,
        CheckConstraint("number_winner_guess>=0"),
        nullable=False,
        default=0,
    )

    points: Mapped[float] = mapped_column(
        sa.Float,
        CheckConstraint("points>=0"),
        nullable=False,
        default=0,
    )

    matches: Mapped[list["MatchModel"]] = relationship(
        "MatchModel",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete",
        passive_deletes=True,
    )

    def __init__(
        self,
        name: str,
        first_name: str,
        last_name: str,
        password: str,
        role: Role,
    ) -> None:
        self.name = name
        self.first_name = first_name
        self.last_name = last_name
        self.password = ph.hash(password)
        self.role = role

    @hybrid_property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @classmethod
    def authenticate(cls, db: "Session", name: str, password: str) -> Optional["UserModel"]:
        user = db.query(cls).filter_by(name=name).first()

        # user not found, verify password with itself to avoid timing attack
        if user is None:
            with contextlib.suppress(VerificationError):
                ph.verify(ph.hash(password), password)

            return None

        # user found
        try:
            ph.verify(user.password, password)
        except VerificationError:
            return None

        return user

    def change_password(self, new_password: str) -> None:
        self.password = ph.hash(new_password)


class ScoreBetModel(Base):
    __tablename__ = "score_bet"

    id: Mapped[UUID] = mapped_column(DB_UUID(), primary_key=True, nullable=False, default=uuid4)

    match_id: Mapped[UUID] = mapped_column(
        DB_UUID(),
        sa.ForeignKey("match.id", ondelete="CASCADE"),
        nullable=False,
    )
    match: Mapped["MatchModel"] = relationship(
        "MatchModel",
        back_populates="score_bets",
        lazy="raise",
    )

    score1: Mapped[int | None] = mapped_column(
        sa.Integer,
        CheckConstraint("score1>=0"),
        default=None,
    )
    score2: Mapped[int | None] = mapped_column(
        sa.Integer,
        CheckConstraint("score2>=0"),
        default=None,
    )

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


class BinaryBetModel(Base):
    __tablename__ = "binary_bet"
    id = mapped_column(DB_UUID(), primary_key=True, nullable=False, default=uuid4)

    match_id: Mapped[UUID] = mapped_column(
        DB_UUID(),
        sa.ForeignKey("match.id", ondelete="CASCADE"),
        nullable=False,
    )
    match: Mapped["MatchModel"] = relationship(
        "MatchModel",
        back_populates="binary_bets",
        lazy="raise",
    )

    is_one_won: Mapped[bool | None] = mapped_column(sa.Boolean, default=None)

    def bet_from_is_one_won(self) -> tuple[None, None] | tuple[bool, bool]:
        if self.is_one_won is None:
            return (None, None)

        return (self.is_one_won, not self.is_one_won)


class BetMapping(Enum):
    SCORE_BET = ScoreBetModel
    BINARY_BET = BinaryBetModel


class MatchReferenceModel(Base):
    __tablename__ = "match_reference"
    id: Mapped[UUID] = mapped_column(DB_UUID(), primary_key=True, nullable=False, default=uuid4)

    group_id: Mapped[UUID] = mapped_column(DB_UUID(), sa.ForeignKey("group.id"), nullable=False)

    index: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    team1_id: Mapped[UUID] = mapped_column(DB_UUID(), sa.ForeignKey("team.id"), nullable=True)
    team2_id: Mapped[UUID] = mapped_column(DB_UUID(), sa.ForeignKey("team.id"), nullable=True)

    bet_type_from_match: Mapped[BetMapping] = mapped_column(SqlEnum(BetMapping), nullable=False)

    __table_args__ = (UniqueConstraint("group_id", "index", name="uq_columns_group_id_index"),)


class MatchModel(Base):
    __tablename__ = "match"
    id: Mapped[UUID] = mapped_column(DB_UUID(), primary_key=True, nullable=False, default=uuid4)

    group_id: Mapped[UUID] = mapped_column(DB_UUID(), sa.ForeignKey("group.id"), nullable=False)
    group: Mapped["GroupModel"] = relationship(
        "GroupModel",
        foreign_keys=group_id,
        backref="matches",
        lazy="raise",
    )

    index: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    team1_id: Mapped[UUID | None] = mapped_column(
        DB_UUID(),
        sa.ForeignKey("team.id"),
        nullable=True,
    )
    team1: Mapped[Optional["TeamModel"]] = relationship(
        "TeamModel",
        foreign_keys=team1_id,
        lazy="raise",
    )

    team2_id: Mapped[UUID | None] = mapped_column(
        DB_UUID(),
        sa.ForeignKey("team.id"),
        nullable=True,
    )
    team2: Mapped[Optional["TeamModel"]] = relationship(
        "TeamModel",
        foreign_keys=team2_id,
        lazy="raise",
    )

    user_id: Mapped[UUID] = mapped_column(
        DB_UUID(),
        sa.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped[UserModel] = relationship("UserModel", foreign_keys=user_id, lazy="raise")

    score_bets: Mapped[list[ScoreBetModel]] = relationship(
        "ScoreBetModel",
        back_populates="match",
        lazy="dynamic",
        cascade="all, delete",
        passive_deletes=True,
    )
    binary_bets: Mapped[list[BinaryBetModel]] = relationship(
        "BinaryBetModel",
        back_populates="match",
        lazy="dynamic",
        cascade="all, delete",
        passive_deletes=True,
    )


class TeamModel(Base):
    __tablename__ = "team"
    id: Mapped[UUID] = mapped_column(DB_UUID(), primary_key=True, nullable=False, default=uuid4)
    code: Mapped[str] = mapped_column(sa.String(10), unique=True, nullable=False)
    description_fr: Mapped[str] = mapped_column(sa.String(100), unique=True, nullable=False)
    description_en: Mapped[str] = mapped_column(sa.String(100), unique=True, nullable=False)
    flag_url: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    internal_flag_url: Mapped[str] = mapped_column(sa.String(300), nullable=False)


class GroupModel(Base):
    __tablename__ = "group"
    id: Mapped[UUID] = mapped_column(DB_UUID(), primary_key=True, nullable=False, default=uuid4)
    code: Mapped[str] = mapped_column(sa.String(2), unique=True, nullable=False)
    description_fr: Mapped[str] = mapped_column(sa.String(100), unique=True, nullable=False)
    description_en: Mapped[str] = mapped_column(sa.String(100), unique=True, nullable=False)
    index: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    phase_id: Mapped[UUID] = mapped_column(DB_UUID(), sa.ForeignKey("phase.id"), nullable=False)
    phase: Mapped["PhaseModel"] = relationship("PhaseModel", backref="groups", lazy="raise")


class PhaseModel(Base):
    __tablename__ = "phase"
    id: Mapped[UUID] = mapped_column(DB_UUID(), primary_key=True, nullable=False, default=uuid4)
    code: Mapped[str] = mapped_column(sa.String(10), unique=True, nullable=False)
    description_fr: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    description_en: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    index: Mapped[int] = mapped_column(sa.Integer, nullable=False)


class GroupPositionModel(Base):
    __tablename__ = "group_position"
    id: Mapped[UUID] = mapped_column(DB_UUID(), primary_key=True, nullable=False, default=uuid4)
    won: Mapped[int] = mapped_column(
        sa.Integer,
        CheckConstraint("won>=0"),
        nullable=False,
        default=0,
    )
    drawn: Mapped[int] = mapped_column(
        sa.Integer,
        CheckConstraint("drawn>=0"),
        nullable=False,
        default=0,
    )
    lost: Mapped[int] = mapped_column(
        sa.Integer,
        CheckConstraint("lost>=0"),
        nullable=False,
        default=0,
    )
    goals_for: Mapped[int] = mapped_column(
        sa.Integer,
        CheckConstraint("goals_for>=0"),
        nullable=False,
        default=0,
    )
    goals_against: Mapped[int] = mapped_column(
        sa.Integer,
        CheckConstraint("goals_against>=0"),
        nullable=False,
        default=0,
    )

    need_recomputation = mapped_column(sa.Boolean, nullable=False, default=False)

    user_id: Mapped[UUID] = mapped_column(
        DB_UUID(),
        sa.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )

    team_id: Mapped[UUID] = mapped_column(
        DB_UUID(),
        sa.ForeignKey("team.id"),
        nullable=False,
    )
    team: Mapped[TeamModel] = relationship("TeamModel", lazy="raise")

    group_id: Mapped[UUID] = mapped_column(
        DB_UUID(),
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
