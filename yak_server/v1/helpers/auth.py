import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, PyJWTError
from sqlalchemy.orm import Session

from yak_server.config_file import Settings, get_settings
from yak_server.database.models import UserModel
from yak_server.helpers.authentification import decode_bearer_token
from yak_server.v1.helpers.database import get_db
from yak_server.v1.helpers.errors import (
    ExpiredToken,
    InvalidToken,
    UnauthorizedAccessToAdminAPI,
    UserNotFound,
)

security = HTTPBearer(auto_error=False)

NUMBER_ELEMENTS_IN_AUTHORIZATION = 2


def user_from_token(db: Session, secret_key: str, token: str) -> UserModel:
    try:
        data = decode_bearer_token(token, secret_key)
    except ExpiredSignatureError as exc:
        raise ExpiredToken from exc
    except PyJWTError as exc:
        raise InvalidToken from exc

    user = db.query(UserModel).filter_by(id=data["sub"]).first()
    if not user:
        raise UserNotFound(data["sub"])

    return user


def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserModel:
    if token is None:
        raise InvalidToken

    return user_from_token(db, settings.jwt_secret_key, token.credentials)


def get_admin_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserModel:
    user = get_current_user(token, db, settings)

    if user.name != "admin":
        raise UnauthorizedAccessToAdminAPI

    return user
