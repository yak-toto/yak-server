from functools import cache
from typing import Annotated

import pendulum
from pydantic import HttpUrl, PlainValidator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .rules import Rules

PendulumDateTime = Annotated[pendulum.DateTime, PlainValidator(pendulum.parse)]


class Settings(BaseSettings):
    competition: str
    data_folder: str
    rules: Rules
    official_results_url: HttpUrl

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


@cache
def get_settings() -> Settings:
    return Settings()


class LockDatetimeSettings(BaseSettings):
    lock_datetime: PendulumDateTime

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


@cache
def get_lock_datetime() -> pendulum.DateTime:
    return LockDatetimeSettings().lock_datetime  # pragma: no cover


class AuthenticationSettings(BaseSettings):
    jwt_secret_key: str
    jwt_refresh_secret_key: str
    jwt_expiration_time: int
    jwt_refresh_expiration_time: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


@cache
def get_authentication_settings() -> AuthenticationSettings:
    return AuthenticationSettings()  # pragma: no cover
