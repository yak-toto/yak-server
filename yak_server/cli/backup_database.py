#!/usr/bin/env python
import subprocess
from datetime import datetime
from pathlib import Path

import pkg_resources
import requests

from yak_server import create_app


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


def script(app):
    with app.app_context():
        if not app.config.get("BOT_TOKEN") or not app.config.get("CHAT_ID"):
            raise MissingTelegramIdentifier

        backup_location = pkg_resources.resource_filename(__name__, "backup_files")
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
        )

        if result.returncode:
            TelegramSender.send_message(
                app.config["BOT_TOKEN"],
                app.config["CHAT_ID"],
                f"Something went wrong when backup on {backup_date} at {backup_time}",
            )
            return

        with Path(file_name).open(mode="w") as file:
            file.write(str(result.stdout))
            TelegramSender.send_message(
                app.config["BOT_TOKEN"],
                app.config["CHAT_ID"],
                f"Backup done on {backup_date} at {backup_time}",
            )


if __name__ == "__main__":
    app = create_app()
    script(app)
