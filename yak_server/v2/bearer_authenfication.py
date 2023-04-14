from functools import wraps
from typing import TYPE_CHECKING

from jwt import ExpiredSignatureError, PyJWTError

from yak_server.database.models import UserModel
from yak_server.helpers.authentification import decode_bearer_token

from .result import ExpiredToken, InvalidToken, UnauthorizedAccessToAdminAPI

NUMBER_ELEMENTS_IN_AUTHORIZATION = 2

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from yak_server.config_file import Settings


def is_authentificated(f):  # noqa: ANN001, ANN201
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = kwargs["info"].context.request.headers.get("Authorization", "").split()
        db: "Session" = kwargs["info"].context.db
        settings: "Settings" = kwargs["info"].context.settings

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

        kwargs["info"].context.user = user

        return f(*args, **kwargs)

    return _verify


def is_admin_authentificated(f):  # noqa: ANN001, ANN201
    @wraps(f)
    def _verify(*args, **kwargs):
        user: UserModel = kwargs["info"].context.user

        if user.name != "admin":
            return UnauthorizedAccessToAdminAPI()

        return f(*args, **kwargs)

    return _verify
