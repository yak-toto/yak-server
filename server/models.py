import uuid

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from . import db


class User(db.Model):
    id = db.Column(
        db.String(100), primary_key=True, default=lambda: str(uuid.uuid4())
    )  # primary keys are required by SQLAlchemy
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(1000), unique=True, nullable=False)
    points = db.Column(db.Integer)

    matches = db.relationship("Match", backref="user", lazy=False)
    results = db.relationship("Result", backref="user", lazy=False)

    def __init__(self, name, password) -> None:
        self.name = name
        self.password = generate_password_hash(password, method="sha256")
        self.points = 0

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

    def to_dict(self):
        return dict(id=self.id, name=self.name, points=self.points)


class Match(db.Model):
    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    group_name = db.Column(db.String(1))
    team1 = db.Column(db.String(100))
    score1 = db.Column(db.Integer)
    score2 = db.Column(db.Integer)
    team2 = db.Column(db.String(100))

    def to_dict(self):
        return {
            "id": self.id,
            "results": [
                {"team": self.team1, "score": self.score1},
                {"team": self.team2, "score": self.score2},
            ],
        }


class Result(db.Model):
    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    number_match_guess = db.Column(db.Integer)
    number_score_guess = db.Column(db.Integer)
    points = db.Column(db.Integer)

    def to_dict(self):
        return dict(
            id=self.id,
            points=self.points,
            number_match_guess=self.number_match_guess,
            number_score_guess=self.number_score_guess,
        )
