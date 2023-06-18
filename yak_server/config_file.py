from datetime import datetime
from functools import lru_cache
from typing import List
from uuid import UUID

from pydantic import BaseModel, BaseSettings


class RuleContainer(BaseModel):
    id: UUID
    config: dict


class Rules(BaseModel):
    __root__: List[RuleContainer]


class Settings(BaseSettings):
    jwt_secret_key: str
    jwt_expiration_time: int
    competition: str
    lock_datetime: datetime
    base_correct_result: int
    multiplying_factor_correct_result: int
    base_correct_score: int
    multiplying_factor_correct_score: int
    team_qualified: int
    first_team_qualified: int
    data_folder: str
    rules: Rules

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    return Settings()
