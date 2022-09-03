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
    points = db.Column(
        db.Float, CheckConstraint("points>=0"), nullable=False, default=0
    )

    scores = db.relationship(
        "Scores",
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
            "points": round(self.points, 3),
        }


class Matches(db.Model):
    __tablename__ = "match"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )

    phase_id = db.Column(db.String(100), db.ForeignKey("phase.id"), nullable=False)
    phase = db.relationship("Phase", foreign_keys=phase_id, backref="matches")

    match_index = db.Column(db.Integer, nullable=False)

    team1_id = db.Column(db.String(100), db.ForeignKey("team.id"), nullable=False)
    team1 = db.relationship("Team", foreign_keys=team1_id, backref="match1")

    team2_id = db.Column(db.String(100), db.ForeignKey("team.id"), nullable=False)
    team2 = db.relationship("Team", foreign_keys=team2_id, backref="match2")

    scores = db.relationship("Scores", back_populates="match")

    def to_dict(self):
        return {
            "id": self.id,
            "index": self.match_index,
            "phase": self.phase.to_dict(),
            "team1": self.team1.to_dict(),
            "team2": self.team2.to_dict(),
        }


def is_locked(score):
    locked_date = datetime.strptime(
        current_app.config["LOCK_DATETIME"], "%Y-%m-%d %H:%M:%S.%f"
    )
    return score.user.name != "admin" and datetime.now() > locked_date


class Scores(db.Model):
    __tablename__ = "score"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    user_id = db.Column(
        db.String(100), db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    user = db.relationship("User", back_populates="scores")

    match_id = db.Column(db.String(100), db.ForeignKey("match.id"), nullable=False)
    match = db.relationship("Matches", back_populates="scores")

    score1 = db.Column(db.Integer, CheckConstraint("score1>=0"), default=None)
    score2 = db.Column(db.Integer, CheckConstraint("score2>=0"), default=None)

    def is_invalid(self) -> bool:
        return None in (self.score1, self.score2)

    def is_1_win(self) -> bool:
        return not self.is_invalid() and self.score1 > self.score2

    def is_draw(self) -> bool:
        return not self.is_invalid() and self.score1 == self.score2

    def is_2_win(self) -> bool:
        return not self.is_invalid() and self.score1 < self.score2

    def is_same_results(self, other) -> bool:
        return (
            (self.is_1_win() and other.is_1_win())
            or (self.is_draw() and other.is_draw())
            or (self.is_2_win() and other.is_2_win())
        )

    def is_same_scores(self, other) -> bool:
        if self.is_invalid() or other.is_invalid():
            return False
        return self.score1 == other.score1 and self.score2 == other.score2

    def to_dict(self):
        return {
            "id": self.id,
            "match_id": self.match_id,
            "match_index": self.match.match_index,
            "locked": is_locked(self),
            "phase": self.match.phase.to_dict(),
            "team1": {**self.match.team1.to_dict(), "score": self.score1},
            "team2": {**self.match.team2.to_dict(), "score": self.score2},
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


class Phase(db.Model):
    __tablename__ = "phase"
    id = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    code = db.Column(db.String(1), primary_key=True, unique=True, nullable=False)
    phase_description = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), unique=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "phase_description": self.phase_description,
            "description": self.description,
        }
