from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    host: str
    user: str
    password: str
    port: int
    db: str

    model_config = SettingsConfigDict(
        env_file=".env.db",
        env_file_encoding="utf-8",
        env_prefix="postgres_",
    )


@cache
def get_postgres_settings() -> PostgresSettings:
    return PostgresSettings()
