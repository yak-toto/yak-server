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
    number_match_guess = db.Column(db.Integer)
    number_score_guess = db.Column(db.Integer)
    points = db.Column(db.Integer)

    matches = db.relationship("Match", backref="user", lazy=False)

    def __init__(self, name, password) -> None:
        self.name = name
        self.password = generate_password_hash(password, method="sha256")
        self.number_match_guess = 0
        self.number_score_guess = 0
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
    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_name = db.Column(db.String(1))
    team1 = db.Column(db.String(100))
    team2 = db.Column(db.String(100))

    match = db.relationship("Match", backref="match", lazy=False)

    def to_dict(self):
        return dict(
            id=self.id, group_name=self.group_name, teams=[self.team1, self.team2]
        )


class Match(db.Model):
    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=True)
    score1 = db.Column(db.Integer)
    score2 = db.Column(db.Integer)

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
