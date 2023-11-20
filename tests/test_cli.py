from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

import pendulum
import pytest
from starlette.testclient import TestClient

from yak_server.cli.database import (
    BackupError,
    RecordDeletionInProductionError,
    TableDropInProductionError,
    backup_database,
    create_admin,
    delete_database,
    drop_database,
)
from yak_server.helpers.settings import get_settings
from yak_server.v1.helpers.errors import NameAlreadyExists

from .utils import get_random_string
from .utils.mock import MockSettings

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_create_admin(app: "FastAPI") -> None:
    app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=20,
        jwt_secret_key=get_random_string(10),
    )

    client = TestClient(app)

    # Success case : create admin using script and test login is OK
    password_admin = get_random_string(6)

    create_admin(password_admin)

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

    with pytest.raises(NameAlreadyExists):
        create_admin(password_admin)


def test_delete_all_records(production_app: "FastAPI") -> None:
    with pytest.raises(RecordDeletionInProductionError):
        delete_database(production_app)


def test_drop_all_tables(production_app: "FastAPI") -> None:
    with pytest.raises(TableDropInProductionError):
        drop_database(production_app)


def test_backup(monkeypatch: pytest.MonkeyPatch) -> None:
    backup_database()

    list_datetime_backup = sorted(
        pendulum.from_format(
            file.name.replace(".sql", "").replace("yak_toto_backup_", ""), "YYYYMMDD[T]HHmmssZZ"
        )
        for file in (Path(__file__).parents[1] / "yak_server" / "cli" / "backup_files").glob("*")
    )

    # Check that most recent backup file has been created less than 2 seconds ago
    assert pendulum.now("UTC") - list_datetime_backup[-1] <= pendulum.duration(seconds=2)

    # Check BackupError if password is incorrect
    monkeypatch.setattr("yak_server.cli.database.mysql_settings.db", get_random_string(6))

    with pytest.raises(BackupError):
        backup_database()
