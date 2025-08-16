from functools import cache
from typing import TYPE_CHECKING, Annotated

import pendulum
from fastapi import Depends
from pydantic import PlainValidator
from pydantic_settings import BaseSettings, SettingsConfigDict

from yak_server.database.models import CompetitionModel

from .database import get_db

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

PendulumDateTime = Annotated[pendulum.DateTime, PlainValidator(pendulum.parse)]


class Settings(BaseSettings):
    competition: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


@cache
def get_settings() -> Settings:
    # assert False
    return Settings()


class AuthenticationSettings(BaseSettings):
    jwt_secret_key: str
    jwt_refresh_secret_key: str
    jwt_expiration_time: int
    jwt_refresh_expiration_time: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


@cache
def get_authentication_settings() -> AuthenticationSettings:
    return AuthenticationSettings()  # pragma: no cover


def get_competition(
    db: Annotated["Session", Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)]
) -> CompetitionModel:
    competition = db.query(CompetitionModel).filter_by(name=settings.competition).first()

    if competition is None:
        message = f"Competition '{settings.competition}' not found in the database."
        raise ValueError(message)

    return competition


@cache
def get_lock_datetime(
    competition: Annotated[CompetitionModel, Depends(get_competition)],
) -> pendulum.DateTime:
    return competition.lock_datetime  # pragma: no cover
