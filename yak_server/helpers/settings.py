from datetime import datetime
from functools import cache
from typing import Annotated

from fastapi import Depends
from pydantic import AwareDatetime, BaseModel, DirectoryPath
from pydantic_settings import BaseSettings, SettingsConfigDict

from .rules import Rules, load_rules


class Settings(BaseSettings):
    competition: str
    data_folder: DirectoryPath

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="allow", env_nested_delimiter="__"
    )


@cache
def get_settings() -> Settings:
    return Settings()


class CompetitionSettings(BaseModel):
    description_fr: str
    description_en: str


class CommonSettings(BaseModel):
    lock_datetime: AwareDatetime
    competition: CompetitionSettings


@cache
def get_common_settings(settings: Annotated[Settings, Depends(get_settings)]) -> CommonSettings:
    common_file = settings.data_folder / "common.json"

    return CommonSettings.model_validate_json(common_file.read_text())


@cache
def get_lock_datetime(
    common_settings: Annotated[CommonSettings, Depends(get_common_settings)],
) -> datetime:
    return common_settings.lock_datetime


@cache
def get_rules(settings: Annotated[Settings, Depends(get_settings)]) -> Rules:
    return load_rules(settings.data_folder)


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
