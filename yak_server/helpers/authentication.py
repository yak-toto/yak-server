from typing import Annotated, Any
from uuid import UUID

import pendulum
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, PyJWTError
from jwt import decode as jwt_decode
from jwt import encode as jwt_encode
from sqlalchemy.orm import Session

from yak_server.database.models import MatchModel, MatchReferenceModel, ScoreBetModel, UserModel

from .database import get_db
from .errors import (
    ExpiredToken,
    InvalidToken,
    NameAlreadyExistsError,
    UnauthorizedAccessToAdminAPI,
    UserNotFound,
)
from .group_position import create_group_position
from .password_validator import validate_password
from .settings import Settings, get_settings


def encode_bearer_token(
    sub: UUID,
    expiration_time: pendulum.Duration,
    secret_key: str,
) -> str:
    return jwt_encode(
        {
            "sub": str(sub),
            "iat": pendulum.now("UTC"),
            "exp": pendulum.now("UTC") + expiration_time,
        },
        secret_key,
        algorithm="HS512",
    )


def decode_bearer_token(token: str, secret_key: str) -> dict[str, Any]:
    return jwt_decode(token, secret_key, algorithms=["HS512"])


def signup_user(
    db: Session, name: str, first_name: str, last_name: str, password: str
) -> UserModel:
    # Check existing user in db
    existing_user = db.query(UserModel).filter_by(name=name).first()
    if existing_user:
        raise NameAlreadyExistsError(name)

    # Validate password
    validate_password(password)

    # Initialize user and integrate in db
    user = UserModel(name, first_name, last_name, password)
    db.add(user)
    db.flush()

    # Initialize matches and bets and integrate in db
    for match_reference in db.query(MatchReferenceModel).all():
        match = MatchModel(
            team1_id=match_reference.team1_id,
            team2_id=match_reference.team2_id,
            index=match_reference.index,
            group_id=match_reference.group_id,
            user_id=user.id,
        )
        db.add(match)
        db.flush()

        db.add(match_reference.bet_type_from_match.value(match_id=match.id))
        db.flush()

    # Create group position records
    db.add_all(
        create_group_position(
            db.query(ScoreBetModel).join(ScoreBetModel.match).filter_by(user_id=user.id)
        )
    )
    db.commit()

    return user


security = HTTPBearer(auto_error=False)


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
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserModel:
    if token is None:
        raise InvalidToken

    return user_from_token(db, settings.jwt_secret_key, token.credentials)


def get_admin_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserModel:
    user = get_current_user(token, db, settings)

    if user.name != "admin":
        raise UnauthorizedAccessToAdminAPI

    return user
