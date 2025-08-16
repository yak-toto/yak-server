from enum import Enum
from typing import Any
from uuid import UUID

import jwt
import pendulum
from sqlalchemy.orm import Session, selectinload

from yak_server.database.models import (
    MatchModel,
    MatchReferenceModel,
    Role,
    ScoreBetModel,
    UserModel,
)

from .errors import name_already_exists_message
from .group_position import create_group_position
from .password_validator import validate_password


def encode_bearer_token(
    sub: UUID,
    expiration_time: pendulum.Duration,
    secret_key: str,
) -> str:
    return jwt.encode(
        {
            "sub": str(sub),
            "nbf": pendulum.now("UTC") - pendulum.duration(seconds=3),
            "exp": pendulum.now("UTC") + expiration_time,
        },
        secret_key,
        algorithm="HS512",
    )


def decode_bearer_token(token: str, secret_key: str) -> Any:  # noqa: ANN401
    return jwt.decode(token, secret_key, algorithms=["HS512"])


class NameAlreadyExistsError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(name_already_exists_message(name))


def signup_user(
    db: Session, name: str, first_name: str, last_name: str, password: str, role: Role
) -> UserModel:
    # Check existing user in db
    existing_user = db.query(UserModel).filter_by(name=name).first()
    if existing_user:
        raise NameAlreadyExistsError(name)

    # Validate password
    validate_password(password)

    # Initialize user and integrate in db
    user = UserModel(name, first_name, last_name, password, role)
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
            db.query(ScoreBetModel)
            .options(selectinload(ScoreBetModel.match))
            .join(ScoreBetModel.match)
            .filter_by(user_id=user.id)
        )
    )
    db.commit()

    return user


class Permission(Enum):
    """Define different permission levels"""

    USER = "user"  # Basic authenticated user
    ADMIN = "admin"  # Administrative access


def has_permission(user: UserModel, required_permission: Permission) -> bool:
    """Check if user has the required permission level.

    Args:
        user: The user to check permissions for
        required_permission: The permission level required

    Returns:
        True if user has the required permission, False otherwise
    """
    permission_hierarchy = {
        Permission.USER: [Role.USER, Role.ADMIN],
        Permission.ADMIN: [Role.ADMIN],
    }

    return user.role in permission_hierarchy[required_permission]
