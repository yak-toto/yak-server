import typing
from typing import Optional
from typing import Union

import jwt
from flask import current_app
from flask import request
from jwt import ExpiredSignatureError
from server.database.models import UserModel
from strawberry.permission import BasePermission
from strawberry.types import Info

from .schema import ExpiredToken
from .schema import InvalidToken
from .schema import User


class BearerAuthentification(BasePermission):
    message = "User is not authenticated"

    def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        auth_headers = request.headers.get("Authorization", "").split()

        if len(auth_headers) != 2:
            return False

        token = auth_headers[1]
        try:
            data = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
        except Exception:
            return False

        user = UserModel.query.filter_by(id=data["sub"]).first()
        if not user:
            return False

        info.user = user

        return True


def bearer_authentification() -> tuple[
    Optional[User], Optional[list[Union[ExpiredToken, InvalidToken]]]
]:
    auth_headers = request.headers.get("Authorization", "").split()

    if len(auth_headers) != 2:
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

    def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        is_authorized = super().has_permission(source, info, **kwargs)

        return is_authorized and info.user.name == "admin"
