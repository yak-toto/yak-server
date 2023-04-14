import logging
from functools import wraps

from flask import current_app, request
from jwt import ExpiredSignatureError, PyJWTError

from yak_server.database.models import UserModel
from yak_server.helpers.authentification import decode_bearer_token

from .errors import ExpiredToken, InvalidToken, UnauthorizedAccessToAdminAPI, UserNotFound

NUMBER_ELEMENTS_IN_AUTHORIZATION = 2

logger = logging.getLogger(__name__)


def user_from_token(auth_headers, db) -> UserModel:
    if len(auth_headers) != NUMBER_ELEMENTS_IN_AUTHORIZATION or auth_headers[0] != "Bearer":
        raise InvalidToken

    token = auth_headers[1]
    try:
        data = decode_bearer_token(token, current_app.config["SECRET_KEY"])
    except ExpiredSignatureError as exc:
        raise ExpiredToken from exc
    except PyJWTError as exc:
        raise InvalidToken from exc

    user = db.query(UserModel).filter_by(id=data["sub"]).first()
    if not user:
        raise UserNotFound(data["sub"])

    return user


def is_authentificated(f):  # noqa: ANN201
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = request.headers.get("Authorization", "").split()

        user = user_from_token(auth_headers, current_app.db)

        return f(user, *args, **kwargs)

    return _verify


def is_admin_authentificated(f):  # noqa: ANN201
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = request.headers.get("Authorization", "").split()

        db = kwargs["db"]

        user = user_from_token(auth_headers, db)

        if user.name != "admin":
            raise UnauthorizedAccessToAdminAPI

        return f(user, *args, **kwargs)

    return _verify
