import typing
from typing import TYPE_CHECKING, Optional, Union

import jwt
from flask import current_app, request
from jwt import ExpiredSignatureError
from strawberry.permission import BasePermission

if TYPE_CHECKING:
    from strawberry.types import Info

from yak_server.database.models import UserModel

from .schema import ExpiredToken, InvalidToken, User

NUMBER_ELEMENTS_IN_AUTHORIZATION = 2


class BearerAuthentification(BasePermission):
    message = "User is not authenticated"

    def has_permission(self, source: typing.Any, info: "Info", **kwargs) -> bool:
        auth_headers = request.headers.get("Authorization", "").split()

        if len(auth_headers) != NUMBER_ELEMENTS_IN_AUTHORIZATION:
            return False

        token = auth_headers[1]
        try:
            data = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
            )
        except Exception:
            return False

        user = UserModel.query.filter_by(id=data["sub"]).first()
        if not user:
            return False

        info.user = user

        return True


def bearer_authentification() -> (
    tuple[
        Optional[User],
        Optional[list[Union[ExpiredToken, InvalidToken]]],
    ]
):
    auth_headers = request.headers.get("Authorization", "").split()

    if len(auth_headers) != NUMBER_ELEMENTS_IN_AUTHORIZATION:
        return None, [InvalidToken()]

    token = auth_headers[1]
    try:
        data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except ExpiredSignatureError:
        return None, [ExpiredToken()]
    except Exception:
        return None, [InvalidToken()]

    user = UserModel.query.filter_by(id=data["sub"]).first()
    if not user:
        return None, [InvalidToken()]

    return User.from_instance(instance=user), None


class AdminBearerAuthentification(BearerAuthentification):
    message = "Unauthorized access to admin API"

    def has_permission(self, source: typing.Any, info: "Info", **kwargs) -> bool:
        is_authorized = super().has_permission(source, info, **kwargs)

        return is_authorized and info.user.name == "admin"
