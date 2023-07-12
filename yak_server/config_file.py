from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Iterator

from pydantic import BaseModel, RootModel
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


class RuleContainer(BaseModel):
    id: UUID
    config: dict


class Rules(RootModel):
    root: list[RuleContainer]

    def __iter__(self) -> Iterator[RuleContainer]:
        return iter(self.root)

    def append(self, rule: RuleContainer) -> None:
        self.root.append(rule)


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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    return Settings()
