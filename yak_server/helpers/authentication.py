from typing import Any
from uuid import UUID

import pendulum
from jwt import decode as jwt_decode
from jwt import encode as jwt_encode
from sqlmodel import Session, select

from yak_server.database.models3 import MatchModel, MatchReferenceModel, UserModel

from .errors import name_already_exists_message
from .group_position import create_group_position
from .password_validator import validate_password


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


class NameAlreadyExistsError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(name_already_exists_message(name))


def signup_user(
    session: Session, name: str, first_name: str, last_name: str, password: str
) -> UserModel:
    # Check existing user in db
    existing_user = session.exec(select(UserModel).where(UserModel.name == name)).first()

    if existing_user is not None:
        raise NameAlreadyExistsError(name)

    # Validate password
    validate_password(password)

    # Initialize user and integrate in db
    user = UserModel(name=name, first_name=first_name, last_name=last_name, password=password)
    session.add(user)
    session.flush()

    # Initialize matches and bets and integrate in db
    for match_reference in session.exec(select(MatchReferenceModel)).all():
        match = MatchModel(
            team1_id=match_reference.team1_id,
            team2_id=match_reference.team2_id,
            index=match_reference.index,
            group_id=match_reference.group_id,
            user_id=user.id,
        )
        session.add(match)
        session.flush()

        session.add(match_reference.bet_type_from_match.value(match_id=match.id))
        session.flush()

    # Create group position records
    session.add_all(create_group_position(session, user.id))
    session.commit()

    return user
