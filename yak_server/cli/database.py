import json
import logging
import subprocess
from datetime import datetime
from getpass import getpass
from importlib import resources
from pathlib import Path

from yak_server import db
from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    GroupPositionModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    TeamModel,
    UserModel,
)

logger = logging.getLogger(__name__)


class ConfirmPasswordDoesNotMatch(Exception):
    def __init__(self) -> None:
        super().__init__("Password and Confirm Password fields does not match.")


class SignupError(Exception):
    def __init__(self, description) -> None:
        super().__init__(f"Error during signup. {description}")


class RecordDeletionInProduction(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to delete records in production using script. DO NOT DO IT.")


class TableDropInProduction(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to drop database tables in production using script. DO NOT DO IT.")


class BackupError(Exception):
    def __init__(self, description) -> None:
        super().__init__(f"Error during backup. {description}")


def create_database(app):
    db.create_all()


def create_admin(app):
    password = getpass(prompt="Admin user password: ")
    confirm_password = getpass(prompt="Confirm admin password: ")

    if password != confirm_password:
        raise ConfirmPasswordDoesNotMatch

    client = app.test_client()

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": "admin",
            "first_name": "admin",
            "last_name": "admin",
            "password": password,
        },
    )

    if not response_signup.json["ok"]:
        raise SignupError(response_signup.json["description"])


def initialize_database(app):
    DATA_FOLDER = app.config["DATA_FOLDER"]

    with Path(f"{DATA_FOLDER}/phases.json").open() as file:
        phases = json.loads(file.read())

        db.session.add_all(PhaseModel(**phase) for phase in phases)
        db.session.commit()

    with Path(f"{DATA_FOLDER}/groups.json").open() as file:
        groups = json.loads(file.read())

        for group in groups:
            phase = PhaseModel.query.filter_by(code=group["phase_code"]).first()
            group.pop("phase_code")
            group["phase_id"] = phase.id

        db.session.add_all(GroupModel(**group) for group in groups)
        db.session.commit()

    with Path(f"{DATA_FOLDER}/teams.json").open() as file:
        teams = json.loads(file.read())

        db.session.add_all(TeamModel(**team) for team in teams)
        db.session.commit()

    with Path(f"{DATA_FOLDER}/matches.json").open() as file:
        matches = json.loads(file.read())

        for match in matches:
            team1 = TeamModel.query.filter_by(code=match["team1_code"]).first()
            match.pop("team1_code")
            match["team1_id"] = team1.id

            team2 = TeamModel.query.filter_by(code=match["team2_code"]).first()
            match.pop("team2_code")
            match["team2_id"] = team2.id

            group = GroupModel.query.filter_by(code=match["group_code"]).first()
            match.pop("group_code")
            match["group_id"] = group.id

        db.session.add_all(MatchModel(**match) for match in matches)
        db.session.commit()


def backup_database(app):
    with resources.as_file(resources.files("yak_server") / "cli/backup_files") as path:
        backup_location = path

    if not Path(backup_location).exists():
        Path(backup_location).mkdir()

    backup_date, backup_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S").split()

    file_name = f"{backup_location}/yak_toto_backup_{backup_date}T{backup_time}.sql"

    result = subprocess.run(
        [
            "mysqldump",
            app.config["MYSQL_DB"],
            "-u",
            app.config["MYSQL_USER_NAME"],
            f"--password={app.config['MYSQL_PASSWORD']}",
        ],
        capture_output=True,
        encoding="utf-8",
    )

    if result.returncode:
        error_message = (
            f"Something went wrong when backup on {backup_date} at {backup_time}: "
            f"{result.stderr.replace(app.config['MYSQL_PASSWORD'], '********')}"
        )

        logger.error(error_message)

        raise BackupError(error_message)

    with Path(file_name).open(mode="w") as file:
        file.write(result.stdout)
        logger.info(f"Backup done on {backup_date} at {backup_time}")


def delete_database(app):
    if not app.config.get("DEBUG"):
        raise RecordDeletionInProduction

    GroupPositionModel.query.delete()
    ScoreBetModel.query.delete()
    BinaryBetModel.query.delete()
    UserModel.query.delete()
    MatchModel.query.delete()
    GroupModel.query.delete()
    PhaseModel.query.delete()
    TeamModel.query.delete()
    db.session.commit()


def drop_database(app):
    if not app.config.get("DEBUG"):
        raise TableDropInProduction

    db.drop_all()
