from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000), unique=True)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    group_name = db.Column(db.String(1))
    team1 = db.Column(db.String(100))
    score1 = db.Column(db.Integer)
    score2 = db.Column(db.Integer)
    team2 = db.Column(db.String(100))
