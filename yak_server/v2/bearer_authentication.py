from typing import TYPE_CHECKING, Union

from fastapi import Request
from jwt import ExpiredSignatureError, PyJWTError

from yak_server.database.models import UserModel
from yak_server.helpers.authentication import decode_bearer_token

from .result import ExpiredToken, InvalidToken, UnauthorizedAccessToAdminAPI

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from yak_server.v2.context import YakContext


NUMBER_ELEMENTS_IN_AUTHORIZATION = 2


def _authentify(
    authorization_header: str, db: "Session", jwt_secret_key: str
) -> Union[UserModel, ExpiredToken, InvalidToken]:
    auth_headers = authorization_header.split()

    if len(auth_headers) != NUMBER_ELEMENTS_IN_AUTHORIZATION or auth_headers[0] != "Bearer":
        return InvalidToken()

    token = auth_headers[1]
    try:
        data = decode_bearer_token(token, jwt_secret_key)
    except ExpiredSignatureError:
        return ExpiredToken()
    except PyJWTError:
        return InvalidToken()

    user = db.query(UserModel).filter_by(id=data["sub"]).first()

    if user is None:
        return InvalidToken()

    return user


def authentify(context: "YakContext") -> Union[UserModel, ExpiredToken, InvalidToken]:
    if not isinstance(context.request, Request):  # pragma: no cover
        return InvalidToken()

    return _authentify(
        context.request.headers.get("Authorization", ""),
        context.db,
        context.settings.jwt_secret_key,
    )


def _authentify_admin(
    authorization_header: str,
    db: "Session",
    jwt_secret_key: str,
) -> Union[UserModel, ExpiredToken, InvalidToken, UnauthorizedAccessToAdminAPI]:
    result = _authentify(authorization_header, db, jwt_secret_key)

    if not isinstance(result, UserModel):
        return result

    user = result

    if user.name != "admin":
        return UnauthorizedAccessToAdminAPI()

    return user


def authentify_admin(
    context: "YakContext",
) -> Union[UserModel, ExpiredToken, InvalidToken, UnauthorizedAccessToAdminAPI]:
    if not isinstance(context.request, Request):  # pragma: no cover
        return InvalidToken()

    return _authentify_admin(
        context.request.headers.get("Authorization", ""),
        context.db,
        context.settings.jwt_secret_key,
    )
