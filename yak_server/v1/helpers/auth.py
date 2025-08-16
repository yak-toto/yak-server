from functools import partial
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, PyJWTError
from sqlalchemy.orm import Session

from yak_server.database.models import UserModel
from yak_server.helpers.authentication import Permission, decode_bearer_token, has_permission
from yak_server.helpers.database import get_db
from yak_server.helpers.settings import AuthenticationSettings, get_authentication_settings

from .errors import ExpiredToken, InvalidToken, UnauthorizedAccessToAdminAPI, UserNotFound

security = HTTPBearer(auto_error=False)


def user_from_token(db: Session, secret_key: str, access_token: str) -> UserModel:
    try:
        data = decode_bearer_token(access_token, secret_key)
    except ExpiredSignatureError as exc:
        raise ExpiredToken from exc
    except PyJWTError as exc:
        raise InvalidToken from exc

    user = db.query(UserModel).filter_by(id=data["sub"]).first()
    if not user:
        raise UserNotFound(data["sub"])

    return user


def require_permission(
    required_permission: Permission,
    access_token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
    auth_settings: Annotated[AuthenticationSettings, Depends(get_authentication_settings)],
) -> UserModel:
    if access_token is None:
        raise InvalidToken

    user = user_from_token(db, auth_settings.jwt_secret_key, access_token.credentials)

    if not has_permission(user, required_permission):
        raise UnauthorizedAccessToAdminAPI

    return user


require_user = partial(require_permission, Permission.USER)
require_admin = partial(require_permission, Permission.ADMIN)
