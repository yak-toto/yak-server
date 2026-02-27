from datetime import datetime
from functools import cache

from pydantic import AwareDatetime, BaseModel, DirectoryPath
from pydantic_settings import BaseSettings, SettingsConfigDict

from .rules import Rules


class CompetitionSettings(BaseModel):
    description_fr: str
    description_en: str


class Settings(BaseSettings):
    competition: str
    data_folder: DirectoryPath
    rules: Rules
    competition_settings: CompetitionSettings

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="allow", env_nested_delimiter="__"
    )


@cache
def get_settings() -> Settings:
    return Settings()


class LockDatetimeSettings(BaseSettings):
    lock_datetime: AwareDatetime

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


@cache
def get_lock_datetime() -> datetime:
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


class CookieSettings(BaseSettings):
    cookie_secure: bool = True
    cookie_domain: str = ""
    allowed_origins: list[str] = []

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


@cache
def get_cookie_settings() -> CookieSettings:
    return CookieSettings()  # pragma: no cover
