import json
import secrets
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

import pendulum
import typer

from yak_server.database import PostgresSettings
from yak_server.helpers.rules import RULE_MAPPING, Rules


class YesOrNo(str, Enum):
    y = "y"
    n = "n"


class RuleNotDefinedError(Exception):
    def __init__(self, rule_id: UUID) -> None:
        super().__init__(f"Rule not defined: {rule_id}")


def write_env_file(env: dict[str, Any], filename: str) -> None:
    Path(filename).write_text(
        "".join([f"{env_var}={env_value}\n" for env_var, env_value in env.items()]),
        encoding="utf-8",
    )


class EnvBuilder:
    def __init__(self) -> None:
        self.env: dict[str, Any] = {}
        self.env_db: dict[str, Any] = {}

        debug = typer.prompt("DEBUG (y/n)", type=YesOrNo)

        self.debug = debug == YesOrNo.y
        self.env["DEBUG"] = 1 if self.debug else 0

    def setup_db_env(self) -> None:
        host = typer.prompt("POSTGRES HOST", default="127.0.0.1")
        user_name = typer.prompt("POSTGRES USER NAME")
        password = typer.prompt("POSTGRES PASSWORD", hide_input=True)
        port = typer.prompt("POSTGRES PORT", type=int, default=5432)
        db = typer.prompt("POSTGRES DB")

        # try to instantiate pydantic model to check if settings are ok
        PostgresSettings(host=host, user_name=user_name, password=password, port=port, db=db)

        self.env_db["POSTGRES_HOST"] = host
        self.env_db["POSTGRES_USER_NAME"] = user_name
        self.env_db["POSTGRES_PASSWORD"] = password
        self.env_db["POSTGRES_PORT"] = port
        self.env_db["POSTGRES_DB"] = db

    def setup_jwt(self) -> None:
        jwt_expiration_time = typer.prompt("JWT_EXPIRATION_TIME")

        self.env["JWT_EXPIRATION_TIME"] = jwt_expiration_time
        self.env["JWT_SECRET_KEY"] = secrets.token_hex(128)

    def choose_competition(self) -> None:
        # Select competition to load associated rules
        path = Path(__file__).parents[1] / "data"

        available_competitions = sorted(
            (competition.stem for competition in path.glob("*")), key=lambda x: x.split("_")[-1]
        )

        for index, competition in enumerate(available_competitions, 1):
            print(f"{index} - {competition}")

        competition_choice: int = typer.prompt("Choose your competition", type=int)

        competition = available_competitions[competition_choice - 1]
        self.env["COMPETITION"] = competition

        data_folder = path / competition
        self.env["DATA_FOLDER"] = data_folder

        # Load rules in environment
        rules_list: dict[str, Any] = {}

        for rule_file in Path(data_folder, "rules").glob("*.json"):
            rule_id = UUID(rule_file.stem)

            if rule_id not in RULE_MAPPING:
                raise RuleNotDefinedError(rule_id)

            rule_name = RULE_MAPPING[rule_id].attribute

            rules_list[rule_name] = json.loads(rule_file.read_text())

        rules = Rules.model_validate(rules_list)
        self.env["RULES"] = rules.model_dump_json(exclude_unset=True)

        # Load lock datetime
        common_settings = json.loads((data_folder / "common.json").read_text())

        self.env["LOCK_DATETIME"] = pendulum.parse(
            common_settings["lock_datetime"]
        ).to_iso8601_string()
        self.env["OFFICIAL_RESULTS_URL"] = common_settings["official_results_url"]

    def write(self) -> None:
        write_env_file(self.env, ".env")
        write_env_file(self.env_db, ".env.db")


def init_env() -> None:
    env_builder = EnvBuilder()
    env_builder.setup_db_env()
    env_builder.setup_jwt()
    env_builder.choose_competition()

    env_builder.write()
