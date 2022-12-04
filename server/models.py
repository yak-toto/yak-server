import uuid
from datetime import datetime

from flask import current_app
from sqlalchemy import CheckConstraint
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from . import db


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    name = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    number_match_guess = db.Column(
        db.Integer, CheckConstraint("number_match_guess>=0"), nullable=False, default=0
    )
    number_score_guess = db.Column(
        db.Integer, CheckConstraint("number_score_guess>=0"), nullable=False, default=0
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
        db.Float, CheckConstraint("points>=0"), nullable=False, default=0
    )

    bets = db.relationship(
        "ScoreBet",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete",
        passive_deletes=True,
    )

    binary_bets = db.relationship(
        "BinaryBet",
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
    def authenticate(cls, **kwargs):
        name = kwargs.get("name")
        password = kwargs.get("password")

        if not name or not password:
            return None

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
            "id": self.id,
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
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


class Match(db.Model):
    __tablename__ = "match"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )

    group_id = db.Column(db.String(100), db.ForeignKey("group.id"), nullable=False)
    group = db.relationship("Group", foreign_keys=group_id, backref="matches")

    index = db.Column(db.Integer, nullable=False)

    team1_id = db.Column(db.String(100), db.ForeignKey("team.id"), nullable=False)
    team1 = db.relationship("Team", foreign_keys=team1_id, backref="match1")

    team2_id = db.Column(db.String(100), db.ForeignKey("team.id"), nullable=False)
    team2 = db.relationship("Team", foreign_keys=team2_id, backref="match2")

    bets = db.relationship("ScoreBet", back_populates="match")
    binary_bets = db.relationship("BinaryBet", back_populates="match")

    def to_dict(self):
        return {
            "id": self.id,
            "index": self.index,
            "group": self.group.to_dict(),
            "team1": self.team1.to_dict(),
            "team2": self.team2.to_dict(),
        }

    def to_dict_with_group_id(self):
        return {
            "id": self.id,
            "index": self.index,
            "group": {"id": self.group_id},
            "team1": self.team1.to_dict(),
            "team2": self.team2.to_dict(),
        }

    def to_dict_without_group(self):
        return {
            "id": self.id,
            "index": self.index,
            "team1": self.team1.to_dict(),
            "team2": self.team2.to_dict(),
        }


def is_locked(score):
    locked_date = datetime.strptime(
        current_app.config["LOCK_DATETIME"], "%Y-%m-%d %H:%M:%S.%f"
    )
    if score.match.group.phase.code == "FINAL":
        locked_date_final_phase = datetime.strptime(
            current_app.config["LOCK_DATETIME_FINAL_PHASE"], "%Y-%m-%d %H:%M:%S.%f"
        )

        return score.user.name != "admin" and datetime.now() > locked_date_final_phase

    return score.user.name != "admin" and datetime.now() > locked_date


def is_phase_locked(phase_code, user_name):
    if phase_code == "FINAL":
        locked_date_final_phase = datetime.strptime(
            current_app.config["LOCK_DATETIME_FINAL_PHASE"], "%Y-%m-%d %H:%M:%S.%f"
        )

        return user_name != "admin" and datetime.now() > locked_date_final_phase

    return False


class ScoreBet(db.Model):
    __tablename__ = "score_bet"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    user_id = db.Column(
        db.String(100), db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    user = db.relationship("User", back_populates="bets")

    match_id = db.Column(db.String(100), db.ForeignKey("match.id"), nullable=False)
    match = db.relationship("Match", back_populates="bets")

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

    def to_dict(self):
        return {
            "id": self.id,
            "match_id": self.match_id,
            "index": self.match.index,
            "locked": is_locked(self),
            "group": self.match.group.to_dict(),
            "team1": self.match.team1.to_dict() | {"score": self.score1},
            "team2": self.match.team2.to_dict() | {"score": self.score2},
        }

    def to_dict_with_group_id(self):
        return {
            "id": self.id,
            "match_id": self.match_id,
            "index": self.match.index,
            "locked": is_locked(self),
            "group": {"id": self.match.group_id},
            "team1": self.match.team1.to_dict() | {"score": self.score1},
            "team2": self.match.team2.to_dict() | {"score": self.score2},
        }

    def to_dict_without_group(self):
        return {
            "id": self.id,
            "match_id": self.match_id,
            "index": self.match.index,
            "locked": is_locked(self),
            "team1": self.match.team1.to_dict() | {"score": self.score1},
            "team2": self.match.team2.to_dict() | {"score": self.score2},
        }


class BinaryBet(db.Model):
    __tablename__ = "binary_bet"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    user_id = db.Column(
        db.String(100), db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    user = db.relationship("User", back_populates="binary_bets")

    match_id = db.Column(db.String(100), db.ForeignKey("match.id"), nullable=False)
    match = db.relationship("Match", back_populates="binary_bets")

    is_one_won = db.Column(db.Boolean, default=None)

    def bet_from_is_one_won(self):
        if self.is_one_won is None:
            return (None, None)

        return (self.is_one_won, not self.is_one_won)

    def to_dict(self):
        bet_results = self.bet_from_is_one_won()

        return {
            "id": self.id,
            "match_id": self.match_id,
            "index": self.match.index,
            "locked": is_locked(self),
            "group": self.match.group.to_dict(),
            "team1": self.match.team1.to_dict() | {"won": bet_results[0]},
            "team2": self.match.team2.to_dict() | {"won": bet_results[1]},
        }

    def to_dict_with_group_id(self):
        bet_results = self.bet_from_is_one_won()

        return {
            "id": self.id,
            "match_id": self.match_id,
            "index": self.match.index,
            "locked": is_locked(self),
            "group": {"id": self.match.group_id},
            "team1": self.match.team1.to_dict() | {"won": bet_results[0]},
            "team2": self.match.team2.to_dict() | {"won": bet_results[1]},
        }

    def to_dict_without_group(self):
        bet_results = self.bet_from_is_one_won()

        return {
            "id": self.id,
            "match_id": self.match_id,
            "index": self.match.index,
            "locked": is_locked(self),
            "team1": self.match.team1.to_dict() | {"won": bet_results[0]},
            "team2": self.match.team2.to_dict() | {"won": bet_results[1]},
        }


class Team(db.Model):
    __tablename__ = "team"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    code = db.Column(db.String(10), unique=True, nullable=False)
    description = db.Column(db.String(100), unique=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "code": self.code, "description": self.description}


class Group(db.Model):
    __tablename__ = "group"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    code = db.Column(db.String(1), primary_key=True, unique=True, nullable=False)
    description = db.Column(db.String(100), unique=True, nullable=False)

    phase_id = db.Column(db.String(100), db.ForeignKey("phase.id"), nullable=False)
    phase = db.relationship("Phase", foreign_keys=phase_id)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "phase": self.phase.to_dict(),
            "description": self.description,
        }

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


class Phase(db.Model):
    __tablename__ = "phase"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    code = db.Column(db.String(10), primary_key=True, unique=True, nullable=False)
    description = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "description": self.description,
        }
