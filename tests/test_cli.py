from datetime import datetime, timedelta
from http import HTTPStatus
from importlib import resources
from unittest.mock import Mock

import pytest
from dateutil import parser

from yak_server.cli.database import (
    BackupError,
    ConfirmPasswordDoesNotMatch,
    RecordDeletionInProduction,
    SignupError,
    TableDropInProduction,
    backup_database,
    create_admin,
    delete_database,
    drop_database,
)

from .test_utils import get_random_string


def test_create_admin(client, app, monkeypatch):
    # Error case : password and confirm password does not match
    mock_password_does_not_match = Mock(
        side_effect=[
            lambda prompt: get_random_string(6),
            lambda prompt: get_random_string(8),
        ],
    )

    monkeypatch.setattr("yak_server.cli.database.getpass", mock_password_does_not_match)

    with pytest.raises(ConfirmPasswordDoesNotMatch):
        create_admin(app)

    # Success case : create admin using script and test login is OK
    password_admin = get_random_string(6)

    monkeypatch.setattr("yak_server.cli.database.getpass", lambda prompt: password_admin)

    create_admin(app)

    response_login = client.post(
        "/api/v1/users/login",
        json={
            "name": "admin",
            "password": password_admin,
        },
    )

    assert response_login.status_code == HTTPStatus.CREATED

    # Error case : check an exception is raised
    # if signup call is KO (Here admin already exists in db)
    password_admin = get_random_string(6)

    monkeypatch.setattr("yak_server.cli.database.getpass", lambda prompt: password_admin)

    with pytest.raises(SignupError):
        create_admin(app)


def test_delete_all_records(production_app):
    with pytest.raises(RecordDeletionInProduction):
        delete_database(production_app)


def test_drop_all_tables(production_app):
    with pytest.raises(TableDropInProduction):
        drop_database(production_app)


def test_backup(app):
    backup_database(app)

    list_datetime_backup = sorted(
        parser.parse(str(file).split("_")[-1].split(".")[0])
        for file in (resources.files("yak_server") / "cli/backup_files").iterdir()
    )

    # Check that most recent backup has been done 1 second ago
    assert datetime.now() - list_datetime_backup[-1] <= timedelta(seconds=1)

    # Check BackupError if password is incorrect
    old_password = app.config["MYSQL_PASSWORD"]
    app.config["MYSQL_PASSWORD"] = get_random_string(6)

    with pytest.raises(BackupError):
        backup_database(app)

    app.config["MYSQL_PASSWORD"] = old_password
