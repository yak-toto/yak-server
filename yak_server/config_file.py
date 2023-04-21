import json
import sys
from configparser import ConfigParser
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict

from dateutil import parser
from pydantic import BaseModel, BaseSettings
from sqlalchemy.orm import Session

from yak_server.database.models import UserModel

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources

from yak_server.helpers.rules import compute_finale_phase_from_group_rank


class RuleContainer(BaseModel):
    config: dict
    function: Callable[[Session, UserModel, dict], None]


RULE_MAPPING = {
    "492345de-8d4a-45b6-8b94-d219f2b0c3e9": compute_finale_phase_from_group_rank,
}


class RuleNotDefined(Exception):
    def __init__(self, rule_id: str) -> None:
        super().__init__(f"Rule not defined: {rule_id}")


class Settings(BaseSettings):
    jwt_secret_key: str
    jwt_expiration_time: int
    competition: str
    lock_datetime: datetime = datetime.now(tz=timezone.utc)
    base_correct_result: int = 0
    multiplying_factor_correct_result: int = 0
    base_correct_score: int = 0
    multiplying_factor_correct_score: int = 0
    team_qualified: int = 0
    first_team_qualified: int = 0
    data_folder: str = ""
    rules: Dict[str, RuleContainer] = {}

    def load_config(self) -> None:
        with resources.as_file(resources.files("yak_server") / "data" / self.competition) as path:
            data_folder = path

        rules = {}

        for rule_file in Path(f"{data_folder}/rules").glob("*.json"):
            rule_id = rule_file.stem

            if rule_id not in RULE_MAPPING:
                raise RuleNotDefined(rule_id)

            with rule_file.open() as rule_content:
                rules[rule_id] = RuleContainer(
                    config=json.loads(rule_content.read()),
                    function=RULE_MAPPING[rule_id],
                )

        config = ConfigParser()
        config.read(f"{data_folder}/config.ini")

        self.lock_datetime = parser.parse(config.get("locking", "datetime"))
        self.base_correct_result = config.getint("points", "base_correct_result")
        self.multiplying_factor_correct_result = config.getint(
            "points",
            "multiplying_factor_correct_result",
        )
        self.base_correct_score = config.getint("points", "base_correct_score")
        self.multiplying_factor_correct_score = config.getint(
            "points",
            "multiplying_factor_correct_score",
        )
        self.team_qualified = config.getint("points", "team_qualified")
        self.first_team_qualified = config.getint("points", "first_team_qualified")
        self.data_folder = data_folder
        self.rules = rules

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    settings = Settings()
    settings.load_config()

    return settings
