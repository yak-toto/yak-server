from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from starlette.testclient import TestClient

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.database import (
    RecordDeletionInProductionError,
    TableDropInProductionError,
    create_admin,
    delete_database,
    drop_database,
)
from yak_server.helpers.authentication import NameAlreadyExistsError
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_create_admin(app: "FastAPI") -> None:
    app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=100,
        jwt_secret_key=get_random_string(10),
    )

    client = TestClient(app)

    # Success case : create admin using script and test login is OK
    password_admin = get_random_string(10)

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
    password_admin = get_random_string(10)

    with pytest.raises(NameAlreadyExistsError):
        create_admin(password_admin)


def test_delete_all_records(production_app: "FastAPI") -> None:
    with pytest.raises(RecordDeletionInProductionError):
        delete_database(production_app)


def test_drop_all_tables(production_app: "FastAPI") -> None:
    with pytest.raises(TableDropInProductionError):
        drop_database(production_app)
