import logging
from datetime import timedelta
from http import HTTPStatus

from flask import Blueprint, current_app, request

from yak_server import db
from yak_server.database.models import GroupModel, MatchModel, PhaseModel, ScoreBetModel, UserModel
from yak_server.helpers.authentification import encode_bearer_token
from yak_server.helpers.group_position import create_group_position
from yak_server.helpers.logging import (
    logged_in_successfully,
    modify_locking_rights,
    modify_password_successfully,
    signed_up_successfully,
)

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

logger = logging.getLogger(__name__)


@auth.post(f"/{GLOBAL_ENDPOINT}/{VERSION}/users/login")
def login_post():
    data = request.get_json()
    user = UserModel.authenticate(**data)

    if not user:
        raise InvalidCredentials

    token = encode_bearer_token(
        sub=user.id,
        expiration_time=timedelta(seconds=current_app.config["JWT_EXPIRATION_TIME"]),
        secret_key=current_app.config["SECRET_KEY"],
    )

    logger.info(logged_in_successfully(user.name))

    return success_response(HTTPStatus.CREATED, user.to_user_dict() | {"token": token})


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
        ScoreBetModel(user_id=user.id, match_id=match.id)
        for match in MatchModel.query.join(MatchModel.group)
        .join(GroupModel.phase)
        .filter(PhaseModel.code == "GROUP")
    )
    db.session.commit()

    # Create group position records
    db.session.add_all(create_group_position(ScoreBetModel.query.filter_by(user_id=user.id)))
    db.session.commit()

    token = encode_bearer_token(
        sub=user.id,
        expiration_time=timedelta(seconds=current_app.config["JWT_EXPIRATION_TIME"]),
        secret_key=current_app.config["SECRET_KEY"],
    )

    logger.info(signed_up_successfully(user.name))

    return success_response(HTTPStatus.CREATED, user.to_user_dict() | {"token": token})


@auth.patch(f"/{GLOBAL_ENDPOINT}/{VERSION}/users/<string:user_id>")
@token_required
def patch_user(current_user, user_id):
    if current_user.name != "admin":
        raise UnauthorizedAccessToAdminAPI

    body = request.get_json()

    if "password" not in body and "lock" not in body:
        raise WrongInputs

    user = UserModel.query.filter_by(id=user_id).first()
    if not user:
        raise UserNotFound

    if "password" in body:
        user.change_password(body["password"])

        db.session.commit()

        logger.info(modify_password_successfully(user.name))

    if "lock" in body:
        user.locked = body["lock"]
        db.session.commit()

        logger.info(modify_locking_rights(user.name, body["lock"]))

    return success_response(HTTPStatus.OK, user.to_user_dict())


@auth.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/current_user")
@token_required
def current_user(current_user):
    return success_response(HTTPStatus.OK, current_user.to_user_dict())


@auth.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/users")
@token_required
def get_users(current_user):
    if current_user.name != "admin":
        raise UnauthorizedAccessToAdminAPI

    return success_response(HTTPStatus.OK, [user.to_user_dict() for user in UserModel.query.all()])


@auth.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/users/<string:user_id>")
@token_required
def get_user(current_user, user_id):
    if current_user.name != "admin":
        raise UnauthorizedAccessToAdminAPI

    user = UserModel.query.filter_by(id=user_id).first()

    if not user:
        raise UserNotFound

    return success_response(HTTPStatus.OK, user.to_user_dict())
