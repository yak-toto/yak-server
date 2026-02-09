from functools import partial
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, PyJWTError
from sqlalchemy.orm import Session

from yak_server.database.models import UserModel
from yak_server.helpers.authentication import Permission, decode_bearer_token, has_permission
from yak_server.helpers.cookies import ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE
from yak_server.helpers.database import get_db
from yak_server.helpers.settings import AuthenticationSettings, get_authentication_settings
from yak_server.v1.models.users import RefreshIn

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


def _extract_token(
    request: Request,
    access_token: HTTPAuthorizationCredentials | None,
) -> str | None:
    if access_token is not None:
        return access_token.credentials

    return request.cookies.get(ACCESS_TOKEN_COOKIE)


def require_permission(
    required_permission: Permission,
    request: Request,
    access_token: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
    auth_settings: Annotated[AuthenticationSettings, Depends(get_authentication_settings)],
) -> UserModel:
    token = _extract_token(request, access_token)

    if token is None:
        raise InvalidToken

    user = user_from_token(db, auth_settings.jwt_secret_key, token)

    if not has_permission(user, required_permission):
        raise UnauthorizedAccessToAdminAPI

    return user


require_user = partial(require_permission, Permission.USER)
require_admin = partial(require_permission, Permission.ADMIN)


def require_refresh_token(request: Request, refresh_in: RefreshIn | None = None) -> str:
    if refresh_in and refresh_in.refresh_token:
        return refresh_in.refresh_token

    token = request.cookies.get(REFRESH_TOKEN_COOKIE)

    if token is None:
        raise InvalidToken

    return token
