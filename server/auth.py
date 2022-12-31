from datetime import datetime
from datetime import timedelta

import jwt
from flask import Blueprint
from flask import current_app
from flask import request

from . import db
from .models import Match
from .models import ScoreBet
from .models import User
from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.errors import InvalidCredentials
from .utils.errors import NameAlreadyExists
from .utils.errors import UnauthorizedAccessToAdminAPI
from .utils.errors import UserNotFound
from .utils.errors import WrongInputs
from .utils.flask_utils import success_response
from .utils.telegram_sender import send_message

auth = Blueprint("auth", __name__)


@auth.post(f"/{GLOBAL_ENDPOINT}/{VERSION}/users/login")
def login_post():
    data = request.get_json()
    user = User.authenticate(**data)

    if not user:
        raise InvalidCredentials()

    send_message(f"User {user.name} login.")

    token = jwt.encode(
        {
            "sub": user.id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=30),
        },
        current_app.config["SECRET_KEY"],
    )
    return success_response(201, user.to_user_dict() | {"token": token})


@auth.post(f"/{GLOBAL_ENDPOINT}/{VERSION}/users/signup")
def signup_post():
    data = request.get_json()

    # Check existing user in db
    existing_user = User.query.filter_by(name=data["name"]).first()
    if existing_user:
        raise NameAlreadyExists(data["name"])

    # Initialize user and integrate in db
    user = User(**data)
    db.session.add(user)
    db.session.commit()

    # Initialize bets and integrate in db
    db.session.add_all(
        ScoreBet(user_id=user.id, match_id=match.id) for match in Match.query.all()
    )
    db.session.commit()

    send_message(f"User {user.name} created.")

    token = jwt.encode(
        {
            "sub": user.id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=30),
        },
        current_app.config["SECRET_KEY"],
    )

    return success_response(201, user.to_user_dict() | {"token": token})


@auth.patch(f"/{GLOBAL_ENDPOINT}/{VERSION}/users/<string:user_id>")
@token_required
def patch_user(current_user, user_id):
    if current_user.name != "admin":
        raise UnauthorizedAccessToAdminAPI()

    body = request.get_json()

    if not body.get("password"):
        raise WrongInputs()

    user = User.query.filter_by(id=user_id).first()
    if not user:
        raise UserNotFound()

    user.change_password(body["password"])

    db.session.commit()

    return success_response(200, user.to_user_dict())


@auth.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/users")
@token_required
def current_user(current_user):
    return success_response(200, current_user.to_user_dict())
