import logging
import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

import pendulum
from fastapi import APIRouter, Depends, status
from pydantic import UUID4
from sqlalchemy.orm import Session

from yak_server.database.models import (
    MatchModel,
    MatchReferenceModel,
    ScoreBetModel,
    UserModel,
)
from yak_server.helpers.authentication import encode_bearer_token
from yak_server.helpers.database import get_db
from yak_server.helpers.group_position import create_group_position
from yak_server.helpers.logging import (
    logged_in_successfully,
    modify_password_successfully,
    signed_up_successfully,
)
from yak_server.helpers.password_validator import (
    PasswordRequirements,
    PasswordRequirementsError,
    validate_password,
)
from yak_server.helpers.settings import Settings, get_settings
from yak_server.v1.helpers.auth import get_admin_user, get_current_user
from yak_server.v1.helpers.errors import (
    InvalidCredentials,
    NameAlreadyExists,
    UnsatisfiedPasswordRequirements,
    UserNotFound,
)
from yak_server.v1.models.generic import GenericOut
from yak_server.v1.models.users import (
    CurrentUserOut,
    LoginIn,
    LoginOut,
    ModifyUserIn,
    PasswordRequirementsOut,
    SignupIn,
    SignupOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


def signup_user(db: Session, signup_in: SignupIn) -> UserModel:
    # Check existing user in db
    existing_user = db.query(UserModel).filter_by(name=signup_in.name).first()
    if existing_user:
        raise NameAlreadyExists(signup_in.name)

    # Validate password
    try:
        validate_password(signup_in.password)
    except PasswordRequirementsError as password_requirements_error:
        raise UnsatisfiedPasswordRequirements(
            str(password_requirements_error)
        ) from password_requirements_error

    # Initialize user and integrate in db
    user = UserModel(
        signup_in.name,
        signup_in.first_name,
        signup_in.last_name,
        signup_in.password,
    )
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

    logger.info(signed_up_successfully(user.name))

    return user


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
    signup_in: SignupIn,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> GenericOut[SignupOut]:
    user = signup_user(db, signup_in)

    return GenericOut(
        result=SignupOut(
            id=user.id,
            name=user.name,
            token=encode_bearer_token(
                sub=user.id,
                expiration_time=pendulum.duration(seconds=settings.jwt_expiration_time),
                secret_key=settings.jwt_secret_key,
            ),
        ),
    )


@router.get("/signup/password_requirements")
def password_requirements() -> GenericOut[PasswordRequirementsOut]:
    password_requirements = PasswordRequirements()

    return GenericOut(
        result=PasswordRequirementsOut(
            minimum_length=password_requirements.MINIMUM_LENGTH,
            uppercase=password_requirements.UPPERCASE,
            lowercase=password_requirements.LOWERCASE,
            digit=password_requirements.DIGIT,
            no_space=password_requirements.NO_SPACE,
        )
    )


@router.post("/login", status_code=status.HTTP_201_CREATED)
def login(
    login_in: LoginIn,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> GenericOut[LoginOut]:
    user = UserModel.authenticate(db, login_in.name, login_in.password)

    if not user:
        raise InvalidCredentials

    logger.info(logged_in_successfully(user.name))

    return GenericOut(
        result=LoginOut(
            id=user.id,
            name=user.name,
            token=encode_bearer_token(
                sub=user.id,
                expiration_time=pendulum.duration(seconds=settings.jwt_expiration_time),
                secret_key=settings.jwt_secret_key,
            ),
        ),
    )


@router.patch("/{user_id}")
def modify_user(
    user_id: UUID4,
    modify_user_in: ModifyUserIn,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[UserModel, Depends(get_admin_user)],
) -> GenericOut[CurrentUserOut]:
    user = db.query(UserModel).filter_by(id=user_id).first()
    if not user:
        raise UserNotFound(user_id)

    user.change_password(modify_user_in.password)

    db.commit()

    logger.info(modify_password_successfully(user.name))

    return GenericOut(result=CurrentUserOut.model_validate(user))


@router.get("/current")
def current_user(
    user: Annotated[UserModel, Depends(get_current_user)],
) -> GenericOut[CurrentUserOut]:
    return GenericOut(result=CurrentUserOut.model_validate(user))
