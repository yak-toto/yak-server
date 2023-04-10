from functools import wraps

from flask import current_app, request
from jwt import ExpiredSignatureError

from yak_server.database.models import UserModel
from yak_server.helpers.authentification import decode_bearer_token

from .errors import ExpiredToken, InvalidToken, UnauthorizedAccessToAdminAPI, UserNotFound

NUMBER_ELEMENTS_IN_AUTHORIZATION = 2


def user_from_token(auth_headers):
    if len(auth_headers) != NUMBER_ELEMENTS_IN_AUTHORIZATION or auth_headers[0] != "Bearer":
        raise InvalidToken

    token = auth_headers[1]
    try:
        data = decode_bearer_token(token, current_app.config["SECRET_KEY"])
    except ExpiredSignatureError as exc:
        raise ExpiredToken from exc
    except Exception as exc:
        raise InvalidToken from exc

    user = UserModel.query.filter_by(id=data["sub"]).first()
    if not user:
        raise UserNotFound(data["sub"])

    return user


def is_authentificated(f):
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = request.headers.get("Authorization", "").split()

        user = user_from_token(auth_headers)

        return f(user, *args, **kwargs)

    return _verify


def is_admin_authentificated(f):
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = request.headers.get("Authorization", "").split()

        user = user_from_token(auth_headers)

        if user.name != "admin":
            raise UnauthorizedAccessToAdminAPI

        return f(user, *args, **kwargs)

    return _verify
