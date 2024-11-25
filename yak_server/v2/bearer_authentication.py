from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING

from jwt import ExpiredSignatureError, PyJWTError

from yak_server.database.models import UserModel
from yak_server.helpers.authentication import decode_bearer_token

from .result import ExpiredToken, InvalidToken, UnauthorizedAccessToAdminAPI

if TYPE_CHECKING:
    from strawberry.types import Info

    from .context import YakContext

NUMBER_ELEMENTS_IN_AUTHORIZATION = 2


def is_authenticated(f):  # noqa: ANN001, ANN201
    @wraps(f)
    def _verify(*args, info: Info[YakContext, None], **kwargs):  # noqa: ANN002, ANN003, ANN202
        auth_headers = info.context.request.headers.get("Authorization", "").split()
        db = info.context.db
        settings = info.context.settings

        if len(auth_headers) != NUMBER_ELEMENTS_IN_AUTHORIZATION or auth_headers[0] != "Bearer":
            return InvalidToken()

        token = auth_headers[1]
        try:
            data = decode_bearer_token(token, settings.jwt_secret_key)
        except ExpiredSignatureError:
            return ExpiredToken()
        except PyJWTError:
            return InvalidToken()

        user = db.query(UserModel).filter_by(id=data["sub"]).first()
        if not user:
            return InvalidToken()

        info.context.user = user

        return f(*args, info=info, **kwargs)

    return _verify


def is_admin_authenticated(f):  # noqa: ANN001, ANN201
    @wraps(f)
    def _verify(*args, info: Info[YakContext, None], **kwargs):  # noqa: ANN002, ANN003, ANN202
        user = info.context.user

        if user.name != "admin":
            return UnauthorizedAccessToAdminAPI()

        return f(*args, info=info, **kwargs)

    return _verify
