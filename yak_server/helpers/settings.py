from datetime import datetime
from functools import cache
from typing import Annotated

from fastapi import Depends
from pydantic import DirectoryPath
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.orm import Session

from yak_server.database.models import CompetitionConfigModel

from .database import get_db
from .rules import Rules


class MissingCompetitionConfigError(Exception):
    pass


@cache
def get_competition_settings(db: Annotated[Session, Depends(get_db)]) -> CompetitionConfigModel:
    for competition_config in db.query(CompetitionConfigModel).all():
        return competition_config

    raise MissingCompetitionConfigError


class Settings(BaseSettings):
    competition: str
    data_folder: DirectoryPath

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


@cache
def get_settings() -> Settings:
    return Settings()


@cache
def get_lock_datetime(
    competition_settings: Annotated[CompetitionConfigModel, Depends(get_competition_settings)],
) -> datetime:
    return competition_settings.lock_datetime  # pragma: no cover


@cache
def get_rules(
    competition_settings: Annotated[CompetitionConfigModel, Depends(get_competition_settings)],
) -> Rules:
    return Rules.model_validate_json(competition_settings.rules)


class AuthenticationSettings(BaseSettings):
    jwt_secret_key: str
    jwt_refresh_secret_key: str
    jwt_expiration_time: int
    jwt_refresh_expiration_time: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


@cache
def get_authentication_settings() -> AuthenticationSettings:
    return AuthenticationSettings()  # pragma: no cover
