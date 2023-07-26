import json
import logging
import subprocess
from datetime import datetime, timezone
from getpass import getpass
from pathlib import Path
from typing import TYPE_CHECKING

from yak_server.config_file import get_settings
from yak_server.database import Base, SessionLocal, engine, mysql_settings
from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    GroupPositionModel,
    MatchModel,
    MatchReferenceModel,
    PhaseModel,
    ScoreBetModel,
    TeamModel,
    UserModel,
)
from yak_server.v1.models.users import SignupIn
from yak_server.v1.routers.users import signup_user

try:
    import alembic
except ImportError:  # pragma: no cover
    alembic = None


if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


class ConfirmPasswordDoesNotMatch(Exception):
    def __init__(self) -> None:
        super().__init__("Password and Confirm Password fields does not match.")


class RecordDeletionInProduction(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to delete records in production using script. DO NOT DO IT.")


class TableDropInProduction(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to drop database tables in production using script. DO NOT DO IT.")


class BackupError(Exception):
    def __init__(self, description: str) -> None:
        super().__init__(f"Error during backup. {description}")


def create_database() -> None:
    Base.metadata.create_all(bind=engine)


def create_admin() -> None:
    password = getpass(prompt="Admin user password: ")
    confirm_password = getpass(prompt="Confirm admin password: ")

    if password != confirm_password:
        raise ConfirmPasswordDoesNotMatch

    db = SessionLocal()

    _ = signup_user(
        db,
        SignupIn(name="admin", first_name="admin", last_name="admin", password=password),
    )


def initialize_database(app: "FastAPI") -> None:
    db = SessionLocal()

    data_folder = get_settings().data_folder

    with Path(f"{data_folder}/phases.json").open() as file:
        phases = json.loads(file.read())

        db.add_all(PhaseModel(**phase) for phase in phases)
        db.flush()

    with Path(f"{data_folder}/groups.json").open() as file:
        groups = json.loads(file.read())

        for group in groups:
            phase = db.query(PhaseModel).filter_by(code=group["phase_code"]).first()
            group.pop("phase_code")
            group["phase_id"] = phase.id

        db.add_all(GroupModel(**group) for group in groups)
        db.flush()

    with Path(f"{data_folder}/teams.json").open() as file:
        teams = json.loads(file.read())

        for team in teams:
            team["flag_url"] = ""

            team_instance = TeamModel(**team)
            db.add(team_instance)
            db.flush()

            team_instance.flag_url = app.url_path_for(
                "retrieve_team_flag_by_id",
                team_id=team_instance.id,
            )
            db.flush()

    with Path(f"{data_folder}/matches.json").open() as file:
        matches = json.loads(file.read())

        for match in matches:
            if match["team1_code"] is None:
                match["team1_id"] = None
            else:
                team1 = db.query(TeamModel).filter_by(code=match["team1_code"]).first()
                match["team1_id"] = team1.id

            if match["team2_code"] is None:
                match["team2_id"] = None
            else:
                team2 = db.query(TeamModel).filter_by(code=match["team2_code"]).first()
                match["team2_id"] = team2.id

            group = db.query(GroupModel).filter_by(code=match["group_code"]).first()
            match["group_id"] = group.id

            match.pop("team1_code")
            match.pop("team2_code")
            match.pop("group_code")

        db.add_all(MatchReferenceModel(**match) for match in matches)
        db.flush()

    db.commit()


def backup_database() -> None:
    result = subprocess.run(
        [
            "mysqldump",
            mysql_settings.db,
            "-u",
            mysql_settings.user_name,
            "-P",
            str(mysql_settings.port),
            "--protocol=tcp",
            f"--password={mysql_settings.password}",
        ],
        capture_output=True,
        encoding="utf-8",
    )

    backup_datetime = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z")

    if result.returncode:
        error_message = (
            f"Something went wrong when backup on {backup_datetime}: "
            f"{result.stderr.replace(mysql_settings.password, '********')}"
        )

        logger.error(error_message)

        raise BackupError(error_message)

    backup_location = Path(__file__).parents[1] / "cli/backup_files"
    backup_location.mkdir(exist_ok=True)

    file_name = f"{backup_location}/yak_toto_backup_{backup_datetime}.sql"

    with Path(file_name).open(mode="w") as file:
        file.write(result.stdout)
        logger.info(f"Backup done on {backup_datetime}")


def delete_database(app: "FastAPI") -> None:
    if not app.debug:
        raise RecordDeletionInProduction

    db = SessionLocal()

    db.query(GroupPositionModel).delete()
    db.query(ScoreBetModel).delete()
    db.query(BinaryBetModel).delete()
    db.query(UserModel).delete()
    db.query(MatchReferenceModel).delete()
    db.query(MatchModel).delete()
    db.query(GroupModel).delete()
    db.query(PhaseModel).delete()
    db.query(TeamModel).delete()
    db.commit()


def drop_database(app: "FastAPI") -> None:
    if not app.debug:
        raise TableDropInProduction

    Base.metadata.drop_all(bind=engine)


def setup_migration() -> None:
    alembic_ini_path = Path(__file__).parents[2] / "alembic.ini"

    print(
        "To be able to run the database migration scripts, you need to run the following command:",
    )
    print(f"export ALEMBIC_CONFIG='{alembic_ini_path.resolve()}'")
    print()
    print(
        "Follow this link for more informations: "
        "https://alembic.sqlalchemy.org/en/latest/tutorial.html#editing-the-ini-file",
    )

    if alembic is None:  # pragma: no cover
        print()
        print("To enable migration using alembic, please run: pip install alembic")
