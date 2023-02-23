from typing import Optional, Union

from flask import current_app, request
from jwt import ExpiredSignatureError

from yak_server.database.models import UserModel
from yak_server.helpers.authentification import decode_bearer_token

from .result import ExpiredToken, InvalidToken, UnauthorizedAccessToAdminAPI
from .schema import User

NUMBER_ELEMENTS_IN_AUTHORIZATION = 2


def bearer_authentification() -> (
    tuple[
        Optional[User],
        Optional[Union[ExpiredToken, InvalidToken]],
    ]
):
    auth_headers = request.headers.get("Authorization", "").split()

    if len(auth_headers) != NUMBER_ELEMENTS_IN_AUTHORIZATION or auth_headers[0] != "Bearer":
        return None, InvalidToken()

    token = auth_headers[1]
    try:
        data = decode_bearer_token(token, current_app.config["SECRET_KEY"])
    except ExpiredSignatureError:
        return None, ExpiredToken()
    except Exception:
        return None, InvalidToken()

    user = UserModel.query.filter_by(id=data["sub"]).first()
    if not user:
        return None, InvalidToken()

    return User.from_instance(instance=user), None


def admin_bearer_authentification() -> (
    tuple[
        Optional[User],
        Optional[Union[ExpiredToken, InvalidToken, UnauthorizedAccessToAdminAPI]],
    ]
):
    user, authentification_error = bearer_authentification()

    if authentification_error:
        return None, authentification_error

    if user.pseudo != "admin":
        return None, UnauthorizedAccessToAdminAPI()

    return user, None
