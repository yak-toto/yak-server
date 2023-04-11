import logging
from datetime import timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING, Tuple

from flask import Blueprint, current_app, request

from yak_server import db
from yak_server.database.models import MatchModel, MatchReferenceModel, ScoreBetModel, UserModel
from yak_server.helpers.authentification import encode_bearer_token
from yak_server.helpers.group_position import create_group_position
from yak_server.helpers.logging import (
    logged_in_successfully,
    modify_password_successfully,
    signed_up_successfully,
)

from .utils.auth_utils import is_admin_authentificated, is_authentificated
from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import (
    InvalidCredentials,
    NameAlreadyExists,
    UserNotFound,
)
from .utils.flask_utils import success_response
from .utils.schemas import SCHEMA_LOGIN, SCHEMA_PATCH_USER, SCHEMA_SIGNUP
from .utils.validation import validate_body

if TYPE_CHECKING:
    from flask import Response


auth = Blueprint("auth", __name__)

logger = logging.getLogger(__name__)


@auth.post(f"/{GLOBAL_ENDPOINT}/{VERSION}/users/login")
@validate_body(schema=SCHEMA_LOGIN)
def login_post() -> Tuple["Response", int]:
    body = request.get_json()
    user = UserModel.authenticate(body["name"], body["password"])

    if not user:
        raise InvalidCredentials

    token = encode_bearer_token(
        sub=user.id,
        expiration_time=timedelta(seconds=current_app.config["JWT_EXPIRATION_TIME"]),
        secret_key=current_app.config["SECRET_KEY"],
    )

    logger.info(logged_in_successfully(user.name))

    return success_response(HTTPStatus.CREATED, {**user.to_user_dict(), "token": token})


@auth.post(f"/{GLOBAL_ENDPOINT}/{VERSION}/users/signup")
@validate_body(schema=SCHEMA_SIGNUP)
def signup_post() -> Tuple["Response", int]:
    data = request.get_json()

    # Check existing user in db
    existing_user = UserModel.query.filter_by(name=data["name"]).first()
    if existing_user:
        raise NameAlreadyExists(data["name"])

    # Initialize user and integrate in db
    user = UserModel(data["name"], data["first_name"], data["last_name"], data["password"])
    db.session.add(user)
    db.session.flush()

    # Initialize matches and bets and integrate in db
    for match_reference in MatchReferenceModel.query.all():
        match = MatchModel(
            team1_id=match_reference.team1_id,
            team2_id=match_reference.team2_id,
            index=match_reference.index,
            group_id=match_reference.group_id,
        )
        db.session.add(match)
        db.session.flush()

        db.session.add(
            match_reference.bet_type_from_match.value(user_id=user.id, match_id=match.id),
        )
        db.session.flush()

    # Create group position records
    db.session.add_all(create_group_position(ScoreBetModel.query.filter_by(user_id=user.id)))
    db.session.commit()

    token = encode_bearer_token(
        sub=user.id,
        expiration_time=timedelta(seconds=current_app.config["JWT_EXPIRATION_TIME"]),
        secret_key=current_app.config["SECRET_KEY"],
    )

    logger.info(signed_up_successfully(user.name))

    return success_response(HTTPStatus.CREATED, {**user.to_user_dict(), "token": token})


@auth.patch(f"/{GLOBAL_ENDPOINT}/{VERSION}/users/<string:user_id>")
@validate_body(schema=SCHEMA_PATCH_USER)
@is_admin_authentificated
def patch_user(_, user_id) -> Tuple["Response", int]:
    body = request.get_json()

    user = UserModel.query.filter_by(id=user_id).first()
    if not user:
        raise UserNotFound(user_id)

    user.change_password(body["password"])

    db.session.commit()

    logger.info(modify_password_successfully(user.name))

    return success_response(HTTPStatus.OK, user.to_user_dict())


@auth.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/current_user")
@is_authentificated
def current_user(current_user) -> Tuple["Response", int]:
    return success_response(HTTPStatus.OK, current_user.to_user_dict())
