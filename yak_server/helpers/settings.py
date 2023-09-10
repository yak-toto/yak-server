from datetime import datetime
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from .rules import Rules


class Settings(BaseSettings):
    jwt_secret_key: str
    jwt_expiration_time: int
    competition: str
    lock_datetime: datetime
    data_folder: str
    rules: Rules

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    return Settings()
