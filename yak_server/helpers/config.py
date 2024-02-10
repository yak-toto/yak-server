from pydantic_settings import BaseSettings, SettingsConfigDict


class RootConfig(BaseSettings):
    debug: bool = False
    profiling: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")
