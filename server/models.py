import uuid
from sqlalchemy import CheckConstraint

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from . import db


class User(db.Model):
    id = db.Column(
        db.String(100), primary_key=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    name = db.Column(db.String(1000), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    number_match_guess = db.Column(db.Integer, CheckConstraint("number_match_guess>=0"), nullable=False, default=0)
    number_score_guess = db.Column(db.Integer, CheckConstraint("number_score_guess>=0"), nullable=False, default=0)
    points = db.Column(db.Integer, CheckConstraint("points>=0"), nullable=False, default=0)

    matches = db.relationship("Scores", backref="user", lazy=False)

    def __init__(self, name, password) -> None:
        self.name = name
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
        return dict(id=self.id, name=self.name)

    def to_result_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            number_match_guess=self.number_match_guess,
            number_score_guess=self.number_score_guess,
            points=self.points,
        )


class Matches(db.Model):
    id = db.Column(db.String(100), primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    group_name = db.Column(db.String(1), nullable=False)
    team1 = db.Column(db.String(100), nullable=False)
    team2 = db.Column(db.String(100), nullable=False)

    match = db.relationship("Scores", backref="match", lazy=False)

    def to_dict(self):
        return dict(
            id=self.id, group_name=self.group_name, teams=[self.team1, self.team2]
        )


class Scores(db.Model):
    id = db.Column(db.String(100), primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=False)
    score1 = db.Column(db.Integer, CheckConstraint("score1>=0"))
    score2 = db.Column(db.Integer, CheckConstraint("score2>=0"))

    def to_dict(self):
        match = Matches.query.filter_by(id=self.match_id).first()

        return {
            "id": self.id,
            "match_id": self.match_id,
            "group_name": match.group_name,
            "results": [
                {"team": match.team1, "score": self.score1},
                {"team": match.team2, "score": self.score2},
            ],
        }
