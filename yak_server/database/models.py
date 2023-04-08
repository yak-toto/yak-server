from datetime import datetime
from enum import Enum
from uuid import uuid4

from dateutil import parser
from flask import current_app, url_for
from sqlalchemy import CheckConstraint
from sqlalchemy import Enum as SqlEnum
from werkzeug.security import check_password_hash, generate_password_hash

from yak_server import db


class UserModel(db.Model):
    __tablename__ = "user"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid4()),
    )
    name = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    number_match_guess = db.Column(
        db.Integer,
        CheckConstraint("number_match_guess>=0"),
        nullable=False,
        default=0,
    )
    number_score_guess = db.Column(
        db.Integer,
        CheckConstraint("number_score_guess>=0"),
        nullable=False,
        default=0,
    )
    number_qualified_teams_guess = db.Column(
        db.Integer,
        CheckConstraint("number_qualified_teams_guess>=0"),
        nullable=False,
        default=0,
    )
    number_first_qualified_guess = db.Column(
        db.Integer,
        CheckConstraint("number_first_qualified_guess>=0"),
        nullable=False,
        default=0,
    )
    number_quarter_final_guess = db.Column(
        db.Integer,
        CheckConstraint("number_quarter_final_guess>=0"),
        nullable=False,
        default=0,
    )
    number_semi_final_guess = db.Column(
        db.Integer,
        CheckConstraint("number_semi_final_guess>=0"),
        nullable=False,
        default=0,
    )
    number_final_guess = db.Column(
        db.Integer,
        CheckConstraint("number_final_guess>=0"),
        nullable=False,
        default=0,
    )
    number_winner_guess = db.Column(
        db.Integer,
        CheckConstraint("number_winner_guess>=0"),
        nullable=False,
        default=0,
    )

    points = db.Column(
        db.Float,
        CheckConstraint("points>=0"),
        nullable=False,
        default=0,
    )

    score_bets = db.relationship(
        "ScoreBetModel",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete",
        passive_deletes=True,
    )

    binary_bets = db.relationship(
        "BinaryBetModel",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete",
        passive_deletes=True,
    )

    def __init__(self, name, first_name, last_name, password) -> None:
        self.name = name
        self.first_name = first_name
        self.last_name = last_name
        self.password = generate_password_hash(password, method="sha256")

    @classmethod
    def authenticate(cls, name, password):
        user = cls.query.filter_by(name=name).first()
        if not user or not check_password_hash(user.password, password):
            return None

        return user

    def change_password(self, new_password) -> None:
        self.password = generate_password_hash(new_password, method="sha256")

    def to_user_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }

    def to_result_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": f"{self.first_name} {self.last_name}",
            "number_match_guess": self.number_match_guess,
            "number_score_guess": self.number_score_guess,
            "number_qualified_teams_guess": self.number_qualified_teams_guess,
            "number_first_qualified_guess": self.number_first_qualified_guess,
            "number_quarter_final_guess": self.number_quarter_final_guess,
            "number_semi_final_guess": self.number_semi_final_guess,
            "number_final_guess": self.number_final_guess,
            "number_winner_guess": self.number_winner_guess,
            "points": round(self.points, 3),
        }


def is_locked(user_name):
    locked_date = parser.parse(current_app.config["LOCK_DATETIME"])
    return user_name != "admin" and datetime.now() > locked_date


class ScoreBetModel(db.Model):
    __tablename__ = "score_bet"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid4()),
    )
    user_id = db.Column(
        db.String(100),
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    user = db.relationship("UserModel", back_populates="score_bets")

    match_id = db.Column(db.String(100), db.ForeignKey("match.id"), nullable=False)
    match = db.relationship("MatchModel", back_populates="score_bets")

    score1 = db.Column(db.Integer, CheckConstraint("score1>=0"), default=None)
    score2 = db.Column(db.Integer, CheckConstraint("score2>=0"), default=None)

    def is_invalid(self) -> bool:
        return None in (self.score1, self.score2)

    def is_valid(self) -> bool:
        return not self.is_invalid()

    def is_1_win(self) -> bool:
        return self.is_valid() and self.score1 > self.score2

    def is_draw(self) -> bool:
        return self.is_valid() and self.score1 == self.score2

    def is_2_win(self) -> bool:
        return self.is_valid() and self.score1 < self.score2

    def is_same_results(self, other) -> bool:
        return (
            (self.is_1_win() and other.is_1_win())
            or (self.is_draw() and other.is_draw())
            or (self.is_2_win() and other.is_2_win())
        )

    def is_same_scores(self, other) -> bool:
        return (
            self.is_valid()
            and other.is_valid()
            and self.score1 == other.score1
            and self.score2 == other.score2
        )

    def to_dict_with_group_id(self):
        return {
            "id": self.id,
            "index": self.match.index,
            "locked": is_locked(self.user.name),
            "group": {"id": self.match.group_id},
            "team1": {**self.match.team1.to_dict(), "score": self.score1},
            "team2": {**self.match.team2.to_dict(), "score": self.score2},
        }

    def to_dict_without_group(self):
        return {
            "id": self.id,
            "index": self.match.index,
            "locked": is_locked(self.user.name),
            "team1": {**self.match.team1.to_dict(), "score": self.score1},
            "team2": {**self.match.team2.to_dict(), "score": self.score2},
        }


class BinaryBetModel(db.Model):
    __tablename__ = "binary_bet"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid4()),
    )
    user_id = db.Column(
        db.String(100),
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    user = db.relationship("UserModel", back_populates="binary_bets")

    match_id = db.Column(db.String(100), db.ForeignKey("match.id"), nullable=False)
    match = db.relationship("MatchModel", back_populates="binary_bets")

    is_one_won = db.Column(db.Boolean, default=None)

    def bet_from_is_one_won(self):
        if self.is_one_won is None:
            return (None, None)

        return (self.is_one_won, not self.is_one_won)

    def to_dict_with_group_id(self):
        bet_results = self.bet_from_is_one_won()

        team1_dict = (
            {**self.match.team1.to_dict(), "won": bet_results[0]}
            if self.match.team1 is not None
            else None
        )
        team2_dict = (
            {**self.match.team2.to_dict(), "won": bet_results[1]}
            if self.match.team2 is not None
            else None
        )

        return {
            "id": self.id,
            "index": self.match.index,
            "locked": is_locked(self.user.name),
            "group": {"id": self.match.group_id},
            "team1": team1_dict,
            "team2": team2_dict,
        }

    def to_dict_without_group(self):
        bet_results = self.bet_from_is_one_won()

        team1_dict = (
            {**self.match.team1.to_dict(), "won": bet_results[0]}
            if self.match.team1 is not None
            else None
        )
        team2_dict = (
            {**self.match.team2.to_dict(), "won": bet_results[1]}
            if self.match.team2 is not None
            else None
        )

        return {
            "id": self.id,
            "index": self.match.index,
            "locked": is_locked(self.user.name),
            "team1": team1_dict,
            "team2": team2_dict,
        }


class BetMapping(Enum):
    SCORE_BET = ScoreBetModel
    BINARY_BET = BinaryBetModel


class MatchReferenceModel(db.Model):
    __tablename__ = "match_reference"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid4()),
    )

    group_id = db.Column(db.String(100), db.ForeignKey("group.id"), nullable=False)

    index = db.Column(db.Integer, nullable=False)

    team1_id = db.Column(db.String(100), db.ForeignKey("team.id"), nullable=True)
    team2_id = db.Column(db.String(100), db.ForeignKey("team.id"), nullable=True)

    bet_type_from_match = db.Column(SqlEnum(BetMapping), nullable=False)


class MatchModel(db.Model):
    __tablename__ = "match"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid4()),
    )

    group_id = db.Column(db.String(100), db.ForeignKey("group.id"), nullable=False)
    group = db.relationship("GroupModel", foreign_keys=group_id, backref="matches")

    index = db.Column(db.Integer, nullable=False)

    team1_id = db.Column(db.String(100), db.ForeignKey("team.id"), nullable=True)
    team1 = db.relationship("TeamModel", foreign_keys=team1_id)

    team2_id = db.Column(db.String(100), db.ForeignKey("team.id"), nullable=True)
    team2 = db.relationship("TeamModel", foreign_keys=team2_id)

    score_bets = db.relationship("ScoreBetModel", back_populates="match")
    binary_bets = db.relationship("BinaryBetModel", back_populates="match")


class TeamModel(db.Model):
    __tablename__ = "team"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid4()),
    )
    code = db.Column(db.String(10), unique=True, nullable=False)
    description = db.Column(db.String(100), unique=True, nullable=False)
    flag_url = db.Column(db.String(100))

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "description": self.description,
            "flag": {"url": url_for("team.retrieve_team_flag", team_id=self.id)},
        }


class GroupModel(db.Model):
    __tablename__ = "group"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid4()),
    )
    code = db.Column(db.String(1), primary_key=True, unique=True, nullable=False)
    description = db.Column(db.String(100), unique=True, nullable=False)
    index = db.Column(db.Integer, nullable=False)

    phase_id = db.Column(db.String(100), db.ForeignKey("phase.id"), nullable=False)
    phase = db.relationship("PhaseModel", backref="groups")

    def to_dict_with_phase_id(self):
        return {
            "id": self.id,
            "code": self.code,
            "phase": {"id": self.phase_id},
            "description": self.description,
        }

    def to_dict_without_phase(self):
        return {
            "id": self.id,
            "code": self.code,
            "description": self.description,
        }


class PhaseModel(db.Model):
    __tablename__ = "phase"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid4()),
    )
    code = db.Column(db.String(10), primary_key=True, unique=True, nullable=False)
    description = db.Column(db.String(100), nullable=False)
    index = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "description": self.description,
        }


class GroupPositionModel(db.Model):
    __tablename__ = "group_position"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid4()),
    )
    won = db.Column(db.Integer, CheckConstraint("won>=0"), nullable=False, default=0)
    drawn = db.Column(db.Integer, CheckConstraint("drawn>=0"), nullable=False, default=0)
    lost = db.Column(db.Integer, CheckConstraint("lost>=0"), nullable=False, default=0)
    goals_for = db.Column(db.Integer, CheckConstraint("goals_for>=0"), nullable=False, default=0)
    goals_against = db.Column(
        db.Integer,
        CheckConstraint("goals_against>=0"),
        nullable=False,
        default=0,
    )
    need_recomputation = db.Column(db.Boolean, nullable=False, default=False)

    user_id = db.Column(
        db.String(100),
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )

    team_id = db.Column(
        db.String(100),
        db.ForeignKey("team.id"),
        nullable=False,
    )
    team = db.relationship("TeamModel")

    group_id = db.Column(
        db.String(100),
        db.ForeignKey("group.id"),
        nullable=False,
    )

    def to_dict(self):
        return {
            "team": self.team.to_dict(),
            "played": self.won + self.drawn + self.lost,
            "won": self.won,
            "drawn": self.drawn,
            "lost": self.lost,
            "goals_for": self.goals_for,
            "goals_against": self.goals_against,
            "goals_difference": self.goals_for - self.goals_against,
            "points": self.won * 3 + self.drawn,
        }
