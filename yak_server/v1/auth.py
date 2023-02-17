from datetime import datetime, timedelta

import jwt
from flask import Blueprint, current_app, request

from yak_server import db
from yak_server.database.models import MatchModel, ScoreBetModel, UserModel

from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import (
    InvalidCredentials,
    NameAlreadyExists,
    UnauthorizedAccessToAdminAPI,
    UserNotFound,
    WrongInputs,
)
from .utils.flask_utils import success_response

auth = Blueprint("auth", __name__)


@auth.post(f"/{GLOBAL_ENDPOINT}/{VERSION}/users/login")
def login_post():
    data = request.get_json()
    user = UserModel.authenticate(**data)

    if not user:
        raise InvalidCredentials

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
    existing_user = UserModel.query.filter_by(name=data["name"]).first()
    if existing_user:
        raise NameAlreadyExists(data["name"])

    # Initialize user and integrate in db
    user = UserModel(**data)
    db.session.add(user)
    db.session.commit()

    # Initialize bets and integrate in db
    db.session.add_all(
        ScoreBetModel(user_id=user.id, match_id=match.id) for match in MatchModel.query.all()
    )
    db.session.commit()

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
        raise UnauthorizedAccessToAdminAPI

    body = request.get_json()

    if not body.get("password"):
        raise WrongInputs

    user = UserModel.query.filter_by(id=user_id).first()
    if not user:
        raise UserNotFound

    user.change_password(body["password"])

    db.session.commit()

    return success_response(200, user.to_user_dict())


@auth.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/current_user")
@token_required
def current_user(current_user):
    return success_response(200, current_user.to_user_dict())


@auth.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/users")
@token_required
def get_users(current_user):
    if current_user.name != "admin":
        raise UnauthorizedAccessToAdminAPI

    return success_response(200, [user.to_user_dict() for user in UserModel.query.all()])


@auth.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/users/<string:user_id>")
@token_required
def get_user(current_user, user_id):
    if current_user.name != "admin":
        raise UnauthorizedAccessToAdminAPI

    user = UserModel.query.filter_by(id=user_id).first()

    if not user:
        raise UserNotFound

    return success_response(200, user.to_user_dict())
