from datetime import datetime
from datetime import timedelta

import jwt
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from . import db
from .models import User
from .telegram_sender import send_message
from .utils import initialize_matches

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["POST"])
def login_post():
    data = request.get_json()
    user = User.authenticate(**data)

    if not user:
        return jsonify({"message": "Invalid credentials", "authenticated": False}), 401

    send_message(f"User {user.name} login.")

    token = jwt.encode(
        {
            "sub": user.id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=30),
        },
        current_app.config["SECRET_KEY"],
    )
    return jsonify({"token": token})


@auth.route("/signup", methods=["POST"])
def signup_post():
    data = request.get_json()

    # Check existing user in db
    existing_user = User.query.filter_by(name=data["name"]).first()
    if existing_user:
        return jsonify({"message": "Name already exists", "signup": False}), 401

    # Initialize user and integrate in db
    user = User(**data)
    db.session.add(user)
    db.session.commit()

    # Initialize matches and integrate in db
    for match in initialize_matches(user.id):
        db.session.add(match)
    db.session.commit()

    return jsonify(user.to_dict()), 201
