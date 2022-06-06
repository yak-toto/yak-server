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

    def to_dict(self):
        return dict(id=self.id, name=self.name)


class Match(db.Model):
    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(1000))
    group_name = db.Column(db.String(1))
    team1 = db.Column(db.String(100))
    score1 = db.Column(db.Integer)
    score2 = db.Column(db.Integer)
    team2 = db.Column(db.String(100))

    def to_dict(self):
        print({id: self.id, self.team1: self.score1, self.team2: self.score2})
        return {
            "id": self.id,
            "results": [
                {"team": self.team1, "score": self.score1},
                {"team": self.team2, "score": self.score2},
            ],
        }
