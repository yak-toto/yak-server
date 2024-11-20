from functools import cache
from typing import Annotated

import pendulum
from pydantic import HttpUrl, PlainValidator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .rules import Rules

PendulumDateTime = Annotated[pendulum.DateTime, PlainValidator(pendulum.parse)]


class Settings(BaseSettings):
    jwt_secret_key: str
    jwt_expiration_time: int
    competition: str
    lock_datetime: PendulumDateTime
    data_folder: str
    rules: Rules
    official_results_url: HttpUrl

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


@cache
def get_settings() -> Settings:
    return Settings()
