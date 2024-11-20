import json
import secrets
from enum import Enum
from pathlib import Path
from uuid import UUID

import pendulum
import typer

from yak_server.database import MySQLSettings
from yak_server.helpers.rules import RULE_MAPPING
from yak_server.helpers.settings import Rules


class YesOrNo(str, Enum):
    y = "y"
    n = "n"


class RuleNotDefinedError(Exception):
    def __init__(self, rule_id: str) -> None:
        super().__init__(f"Rule not defined: {rule_id}")


def write_env_file(env: dict, filename: str) -> None:
    Path(filename).write_text(
        "".join([f"{env_var}={env_value}\n" for env_var, env_value in env.items()]),
        encoding="utf-8",
    )


class EnvBuilder:
    def __init__(self) -> None:
        self.env = {}
        self.env_mysql = {}

        debug = typer.prompt("DEBUG (y/n)", type=YesOrNo)

        self.debug = debug == YesOrNo.y
        self.env["DEBUG"] = 1 if self.debug else 0

    def setup_profiling(self) -> None:
        if self.debug:
            profiling = typer.prompt("PROFILING (y/n)", type=YesOrNo)

            self.env["PROFILING"] = 1 if profiling == YesOrNo.y else 0

    def setup_mysql_env(self) -> None:
        host = typer.prompt("MYSQL HOST", default="127.0.0.1")
        user_name = typer.prompt("MYSQL USER NAME")
        password = typer.prompt("MYSQL PASSWORD", hide_input=True)
        port = typer.prompt("MYSQL PORT", type=int, default=3306)
        db = typer.prompt("MYSQL DB")

        # try to instance pydantic model to check if settings are ok
        MySQLSettings(host=host, user_name=user_name, password=password, port=port, db=db)

        self.env_mysql["MYSQL_HOST"] = host
        self.env_mysql["MYSQL_USER_NAME"] = user_name
        self.env_mysql["MYSQL_PASSWORD"] = password
        self.env_mysql["MYSQL_PORT"] = port
        self.env_mysql["MYSQL_DB"] = db

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

        competition_choice = typer.prompt("Choose your competition", type=int)

        competition = available_competitions[competition_choice - 1]
        self.env["COMPETITION"] = competition

        data_folder = path / competition
        self.env["DATA_FOLDER"] = data_folder

        # Load rules in environment
        rules_list: dict[str, dict] = {}

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
        write_env_file(self.env_mysql, ".env.mysql")


def init_env() -> None:
    env_builder = EnvBuilder()
    env_builder.setup_profiling()
    env_builder.setup_mysql_env()
    env_builder.setup_jwt()
    env_builder.choose_competition()

    env_builder.write()
