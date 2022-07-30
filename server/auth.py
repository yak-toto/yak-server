from datetime import datetime
from datetime import timedelta

import jwt
from flask import Blueprint
from flask import current_app
from flask import request

from . import db
from .models import Matches
from .models import Scores
from .models import User
from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.errors import invalid_credentials
from .utils.errors import invalid_name
from .utils.flask_utils import failed_response
from .utils.flask_utils import success_response
from .utils.telegram_sender import send_message

auth = Blueprint("auth", __name__)


@auth.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/login", methods=["POST"])
def login_post():
    data = request.get_json()
    user = User.authenticate(**data)

    if not user:
        return failed_response(*invalid_credentials)

    send_message(f"User {user.name} login.")

    token = jwt.encode(
        {
            "sub": user.id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=30),
        },
        current_app.config["SECRET_KEY"],
    )
    return success_response(201, {**user.to_user_dict(), "token": token})


@auth.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/signup", methods=["POST"])
def signup_post():
    data = request.get_json()

    # Check existing user in db
    existing_user = User.query.filter_by(name=data["name"]).first()
    if existing_user:
        return failed_response(*invalid_name)

    # Initialize user and integrate in db
    user = User(**data)
    db.session.add(user)
    db.session.commit()

    # Initialize scores and integrate in db
    for match in Matches.query.all():
        db.session.add(
            Scores(user_id=user.id, match_id=match.id, score1=None, score2=None)
        )
    db.session.commit()

    return success_response(201, user.to_user_dict())


@auth.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/current_user")
@token_required
def current_user(current_user):
    return success_response(200, current_user.to_user_dict())
