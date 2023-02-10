from datetime import datetime, timedelta
from typing import Optional, Union

from flask import current_app, request
from jwt import ExpiredSignatureError
from jwt import decode as jwt_decode
from jwt import encode as jwt_encode

from yak_server.database.models import UserModel

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

    if len(auth_headers) != NUMBER_ELEMENTS_IN_AUTHORIZATION:
        return None, InvalidToken()

    token = auth_headers[1]
    try:
        data = jwt_decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
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


def encode_bearer_token(sub: str, expiration_time: timedelta, secret_key: str) -> str:
    return jwt_encode(
        {
            "sub": sub,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + expiration_time,
        },
        secret_key,
    )
