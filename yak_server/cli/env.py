import json
import secrets
from configparser import ConfigParser
from getpass import getpass
from pathlib import Path
from uuid import UUID

from dateutil import parser

from yak_server.database import MySQLSettings
from yak_server.helpers.rules import RULE_MAPPING
from yak_server.helpers.settings import RuleContainer, Rules


class RuleNotDefined(Exception):
    def __init__(self, rule_id: str) -> None:
        super().__init__(f"Rule not defined: {rule_id}")


class EnvBuilder:
    def __init__(self) -> None:
        self.env = {}
        self.env_mysql = {}

        debug = input("DEBUG (y/n): ")

        self.debug = debug == "y"
        self.env["DEBUG"] = 1 if self.debug else 0

    def setup_profiling(self) -> None:
        if self.debug:
            profiling = input("PROFILING (y/n): ")

            self.env["PROFILING"] = 1 if profiling == "y" else 0

    def setup_mysql_env(self) -> None:
        user_name = input("MYSQL USER NAME: ")
        password = getpass("MYSQL PASSWORD: ")
        port = input("MYSQL PORT (default: 3306): ")
        db = input("MYSQL DB: ")

        # try to instance pydantic model to check if
        # settings are ok
        if not port:
            MySQLSettings(user_name=user_name, password=password, db=db)
        else:
            MySQLSettings(user_name=user_name, password=password, port=port, db=db)

        self.env_mysql["MYSQL_USER_NAME"] = user_name
        self.env_mysql["MYSQL_PASSWORD"] = password
        if port:
            self.env_mysql["MYSQL_PORT"] = port
        self.env_mysql["MYSQL_DB"] = db

    def setup_jwt(self) -> None:
        jwt_expiration_time = input("JWT_EXPIRATION_TIME: ")

        self.env["JWT_EXPIRATION_TIME"] = jwt_expiration_time
        self.env["JWT_SECRET_KEY"] = secrets.token_hex(128)

    def choose_competition(self) -> None:
        # Select competition to load associated rules
        path = Path(__file__).parents[1] / "data"

        available_competitions = [competition.stem for competition in path.glob("*")]

        for index, competition in enumerate(available_competitions, 1):
            print(f"{index} - {competition}")

        competition_choice = int(input("Choose your competition: "))

        competition = available_competitions[competition_choice - 1]

        data_folder = path / competition

        # Load rules in environment
        rules = Rules([])

        for rule_file in Path(f"{data_folder}/rules").glob("*.json"):
            rule_id = UUID(rule_file.stem)

            if rule_id not in RULE_MAPPING:
                raise RuleNotDefined(rule_id)

            with rule_file.open() as rule_content:
                rules.append(
                    RuleContainer(id=rule_id, config=json.loads(rule_content.read())),
                )

        # Load configuration to compute points
        config = ConfigParser()
        config.read(f"{data_folder}/config.ini")

        self.env["COMPETITION"] = competition
        self.env["LOCK_DATETIME"] = parser.parse(config.get("locking", "datetime"))
        self.env["BASE_CORRECT_RESULT"] = config.getint("points", "base_correct_result")
        self.env["MULTIPLYING_FACTOR_CORRECT_RESULT"] = config.getint(
            "points",
            "multiplying_factor_correct_result",
        )
        self.env["BASE_CORRECT_SCORE"] = config.getint("points", "base_correct_score")
        self.env["MULTIPLYING_FACTOR_CORRECT_SCORE"] = config.getint(
            "points",
            "multiplying_factor_correct_score",
        )
        self.env["TEAM_QUALIFIED"] = config.getint("points", "team_qualified")
        self.env["FIRST_TEAM_QUALIFIED"] = config.getint("points", "first_team_qualified")
        self.env["DATA_FOLDER"] = data_folder
        self.env["RULES"] = rules.model_dump_json()

    def write(self) -> None:
        write_env_file(self.env, ".env")
        write_env_file(self.env_mysql, ".env.mysql")


def write_env_file(env: dict, filename: str) -> None:
    with Path(filename).open(mode="w") as file:
        for env_var, env_value in env.items():
            file.write(f"{env_var}={env_value}\n")


def init_env() -> None:
    env_builder = EnvBuilder()
    env_builder.setup_profiling()
    env_builder.setup_mysql_env()
    env_builder.setup_jwt()
    env_builder.choose_competition()

    env_builder.write()
