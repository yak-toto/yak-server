import csv
import subprocess
from datetime import datetime
from getpass import getpass
from pathlib import Path

import pkg_resources
import requests

from yak_server import db
from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    TeamModel,
    UserModel,
)


class ConfirmPasswordDoesNotMatch(Exception):
    def __init__(self) -> None:
        super().__init__("Password and Confirm Password fields does not match.")


class SignupError(Exception):
    def __init__(self, description) -> None:
        super().__init__(f"Error during signup. {description}")


class TelegramSender:
    @staticmethod
    def send_message(bot_token, chat_id, text):
        requests.get(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            params={"chat_id": chat_id, "text": text},
            timeout=10,
        )


class MissingTelegramIdentifier(Exception):
    def __init__(self) -> None:
        super().__init__("Bot token or chat id is missing in flask config. Backup is disabled.")


class RecordDeletionInProduction(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to delete records in production using script. DO NOT DO IT.")


class TableDropInProduction(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to drop database tables in production using script. DO NOT DO IT.")


def create_database(app):
    with app.app_context():
        db.create_all()


def create_admin(app):
    with app.app_context():
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
    with app.app_context():
        DATA_FOLDER = app.config["DATA_FOLDER"]

        with Path(f"{DATA_FOLDER}/phases.csv", newline="").open() as csvfile:
            spamreader = csv.reader(csvfile, delimiter="|")

            for row in spamreader:
                index, code, description = row
                db.session.add(PhaseModel(code=code, description=description, index=index))

            db.session.commit()

        with Path(f"{DATA_FOLDER}/groups.csv", newline="").open() as csvfile:
            spamreader = csv.reader(csvfile, delimiter="|")

            for row in spamreader:
                index, code, phase_code, description = row

                phase = PhaseModel.query.filter_by(code=phase_code).first()

                db.session.add(
                    GroupModel(code=code, phase_id=phase.id, description=description, index=index),
                )

            db.session.commit()

        with Path(f"{DATA_FOLDER}/teams.csv", newline="").open() as csvfile:
            spamreader = csv.reader(csvfile, delimiter="|")

            db.session.add_all(
                TeamModel(
                    code=row[0],
                    description=row[1],
                    flag_url=row[2],
                )
                for row in spamreader
            )
            db.session.commit()

        with Path(f"{DATA_FOLDER}/matches.csv", newline="").open() as csvfile:
            spamreader = csv.reader(csvfile, delimiter="|")

            for row in spamreader:
                group_code, index, team1_code, team2_code = row

                team1 = TeamModel.query.filter_by(code=team1_code).first()
                team2 = TeamModel.query.filter_by(code=team2_code).first()

                group = GroupModel.query.filter_by(code=group_code).first()

                db.session.add(
                    MatchModel(
                        group_id=group.id,
                        team1_id=team1.id,
                        team2_id=team2.id,
                        index=index,
                    ),
                )

            db.session.commit()


def backup_database(app):
    with app.app_context():
        if not app.config.get("BOT_TOKEN") or not app.config.get("CHAT_ID"):
            raise MissingTelegramIdentifier

        backup_location = pkg_resources.resource_filename(__name__, "backup_files")

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
            TelegramSender.send_message(
                app.config["BOT_TOKEN"],
                app.config["CHAT_ID"],
                f"Something went wrong when backup on {backup_date} at {backup_time}",
            )
            return

        with Path(file_name).open(mode="w") as file:
            file.write(result.stdout)
            TelegramSender.send_message(
                app.config["BOT_TOKEN"],
                app.config["CHAT_ID"],
                f"Backup done on {backup_date} at {backup_time}",
            )


def delete_database(app):
    if not app.config.get("DEBUG"):
        raise RecordDeletionInProduction

    with app.app_context():
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

    with app.app_context():
        db.drop_all()
