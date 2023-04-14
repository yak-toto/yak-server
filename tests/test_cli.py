import sys
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import TYPE_CHECKING

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources

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
from yak_server.config_file import get_settings

from .utils import get_random_string
from .utils.mock import create_mock

if TYPE_CHECKING:
    from fastapi import FastAPI
    from starlette.testclient import TestClient


def test_create_admin(app: "FastAPI", client: "TestClient", monkeypatch):
    app.dependency_overrides[get_settings] = create_mock(
        jwt_expiration_time=20,
        jwt_secret_key=get_random_string(10),
    )

    # Error case : password and confirm password does not match
    mock_password_does_not_match = Mock(
        side_effect=[
            lambda prompt: get_random_string(6),  # noqa: ARG005
            lambda prompt: get_random_string(8),  # noqa: ARG005
        ],
    )

    monkeypatch.setattr("yak_server.cli.database.getpass", mock_password_does_not_match)

    with pytest.raises(ConfirmPasswordDoesNotMatch):
        create_admin(app)

    # Success case : create admin using script and test login is OK
    password_admin = get_random_string(6)

    monkeypatch.setattr(
        "yak_server.cli.database.getpass",
        lambda prompt: password_admin,  # noqa: ARG005
    )

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

    monkeypatch.setattr(
        "yak_server.cli.database.getpass",
        lambda prompt: password_admin,  # noqa: ARG005
    )

    with pytest.raises(SignupError):
        create_admin(app)


def test_delete_all_records(production_app):
    with pytest.raises(RecordDeletionInProduction):
        delete_database(production_app)


def test_drop_all_tables(production_app):
    with pytest.raises(TableDropInProduction):
        drop_database(production_app)


def test_backup(monkeypatch):
    backup_database()

    list_datetime_backup = sorted(
        parser.parse(file.name.replace(".sql", "").replace("yak_toto_backup_", ""))
        for file in (resources.files("yak_server") / "cli/backup_files").iterdir()
    )

    # Check that most recent backup has been done 1 second ago
    assert datetime.now(tz=timezone.utc) - list_datetime_backup[-1] <= timedelta(seconds=2)

    # Check BackupError if password is incorrect
    monkeypatch.setattr("yak_server.cli.database.mysql_settings.db", get_random_string(6))

    with pytest.raises(BackupError):
        backup_database()
