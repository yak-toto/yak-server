import logging
from typing import Annotated
from uuid import UUID

import pendulum
from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from pydantic import UUID4
from sqlalchemy.orm import Session

from yak_server.database.models import RefreshTokenModel, UserModel
from yak_server.helpers.authentication import (
    NameAlreadyExistsError,
    add_refresh_token,
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
from yak_server.helpers.settings import (
    AuthenticationSettings,
    get_authentication_settings,
)
from yak_server.v1.helpers.auth import get_admin_user, get_current_user
from yak_server.v1.helpers.errors import (
    ExpiredRefreshToken,
    InvalidCredentials,
    InvalidRefreshToken,
    NameAlreadyExists,
    UnsatisfiedPasswordRequirements,
    UserNotFound,
)
from yak_server.v1.models.generic import ErrorOut, GenericOut, ValidationErrorOut
from yak_server.v1.models.users import (
    CurrentUserOut,
    LoginIn,
    LoginOut,
    ModifyUserIn,
    PasswordRequirementsOut,
    RefreshTokenOut,
    SignupIn,
    SignupOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


def set_refresh_token_cookie(
    response: Response, refresh_token: UUID, max_age: int, *, debug: bool
) -> None:
    secure = not debug

    response.set_cookie(
        key="refresh_token",
        value=str(refresh_token),
        httponly=True,
        max_age=max_age,
        secure=secure,
        samesite="lax",
        path="/",
    )


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorOut},
        status.HTTP_409_CONFLICT: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorOut},
    },
)
def signup(
    signup_in: SignupIn,
    db: Annotated[Session, Depends(get_db)],
    auth_settings: Annotated[AuthenticationSettings, Depends(get_authentication_settings)],
    request: Request,
    response: Response,
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

    refresh_token = add_refresh_token(
        db, user.id, pendulum.duration(seconds=auth_settings.jwt_refresh_expiration_time)
    )

    logger.info(signed_up_successfully(user.name))

    set_refresh_token_cookie(
        response, refresh_token, auth_settings.jwt_refresh_expiration_time, debug=request.app.debug
    )

    return GenericOut(
        result=SignupOut(
            id=user.id,
            name=user.name,
            access_token=encode_bearer_token(
                sub=user.id,
                expiration_time=pendulum.duration(seconds=auth_settings.jwt_expiration_time),
                secret_key=auth_settings.jwt_secret_key,
            ),
        ),
    )


@router.get(
    "/signup/password_requirements",
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorOut}},
)
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


@router.post(
    "/login",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_409_CONFLICT: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorOut},
    },
)
def login(
    login_in: LoginIn,
    db: Annotated[Session, Depends(get_db)],
    auth_settings: Annotated[AuthenticationSettings, Depends(get_authentication_settings)],
    request: Request,
    response: Response,
) -> GenericOut[LoginOut]:
    user = UserModel.authenticate(db, login_in.name, login_in.password)

    if not user:
        raise InvalidCredentials

    refresh_token = add_refresh_token(
        db, user.id, pendulum.duration(seconds=auth_settings.jwt_refresh_expiration_time)
    )

    logger.info(logged_in_successfully(user.name))

    set_refresh_token_cookie(
        response, refresh_token, auth_settings.jwt_refresh_expiration_time, debug=request.app.debug
    )

    return GenericOut(
        result=LoginOut(
            id=user.id,
            name=user.name,
            access_token=encode_bearer_token(
                sub=user.id,
                expiration_time=pendulum.duration(seconds=auth_settings.jwt_expiration_time),
                secret_key=auth_settings.jwt_secret_key,
            ),
        ),
    )


@router.post(
    "/refresh",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorOut},
    },
)
def refresh(
    db: Annotated[Session, Depends(get_db)],
    auth_settings: Annotated[AuthenticationSettings, Depends(get_authentication_settings)],
    refresh_token: Annotated[str, Cookie()],
    request: Request,
    response: Response,
) -> GenericOut[RefreshTokenOut]:
    refresh_token_found = db.query(RefreshTokenModel).filter_by(id=refresh_token).first()

    if refresh_token_found is None:
        raise InvalidRefreshToken

    if pendulum.now("UTC") > refresh_token_found.expiration:
        raise ExpiredRefreshToken

    user_id = refresh_token_found.user_id

    # Issue new access token
    new_access_token = encode_bearer_token(
        sub=user_id,
        expiration_time=pendulum.duration(seconds=auth_settings.jwt_expiration_time),
        secret_key=auth_settings.jwt_secret_key,
    )

    # Rotate refresh token
    new_refresh_token = add_refresh_token(
        db,
        user_id,
        pendulum.duration(seconds=auth_settings.jwt_refresh_expiration_time),
        refresh_token_found,
    )

    set_refresh_token_cookie(
        response,
        new_refresh_token,
        auth_settings.jwt_refresh_expiration_time,
        debug=request.app.debug,
    )

    return GenericOut(result=RefreshTokenOut(access_token=new_access_token))


@router.patch(
    "/{user_id}",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorOut},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorOut},
    },
)
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


@router.get(
    "/current",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorOut},
    },
)
def current_user(
    user: Annotated[UserModel, Depends(get_current_user)],
) -> GenericOut[CurrentUserOut]:
    return GenericOut(result=CurrentUserOut.model_validate(user))
