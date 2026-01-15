from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from starlette.testclient import TestClient

from testing.util import get_random_string
from yak_server.cli.admin import create_admin
from yak_server.cli.database import (
    RecordDeletionInProductionError,
    TableDropInProductionError,
    delete_database,
    drop_database,
)

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy import Engine


def test_create_admin(app_with_valid_jwt_config: "FastAPI", engine_for_test: "Engine") -> None:
    client = TestClient(app_with_valid_jwt_config)

    # Success case : create admin using script and test login is OK
    password_admin = get_random_string(10)

    create_admin(password_admin, engine_for_test)

    response_login = client.post(
        "/api/v1/users/login",
        json={
            "name": "admin",
            "password": password_admin,
        },
    )

    assert response_login.status_code == HTTPStatus.CREATED

    # Success case : if admin already exists in db, it must not fail
    password_admin = get_random_string(10)

    create_admin(password_admin, engine_for_test)


def test_delete_all_records(engine_for_test: "Engine") -> None:
    with pytest.raises(RecordDeletionInProductionError):
        delete_database(engine_for_test, debug=False)


def test_drop_all_tables(engine_for_test: "Engine") -> None:
    with pytest.raises(TableDropInProductionError):
        drop_database(engine_for_test, debug=False)
