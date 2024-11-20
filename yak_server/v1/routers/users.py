import logging
from typing import Annotated

import pendulum
from fastapi import APIRouter, Depends, status
from pydantic import UUID4
from sqlalchemy.orm import Session

from yak_server.database.models import UserModel
from yak_server.helpers.authentication import (
    NameAlreadyExistsError,
    encode_bearer_token,
    signup_user,
)
from yak_server.helpers.database import get_db
from yak_server.helpers.logging_helpers import (
    logged_in_successfully,
    modify_password_successfully,
    signed_up_successfully,
)
from yak_server.helpers.password_validator import (
    PasswordRequirements,
    PasswordRequirementsError,
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


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
    signup_in: SignupIn,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> GenericOut[SignupOut]:
    try:
        user = signup_user(
            db, signup_in.name, signup_in.first_name, signup_in.last_name, signup_in.password
        )
    except PasswordRequirementsError as password_requirements_error:
        raise UnsatisfiedPasswordRequirements(
            str(password_requirements_error)
        ) from password_requirements_error
    except NameAlreadyExistsError as name_already_exists_error:
        raise NameAlreadyExists(signup_in.name) from name_already_exists_error

    logger.info(signed_up_successfully(user.name))

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
