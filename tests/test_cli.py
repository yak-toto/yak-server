from http import HTTPStatus
from unittest.mock import Mock

import pytest

from yak_server.cli.database import (
    ConfirmPasswordDoesNotMatch,
    RecordDeletionInProduction,
    SignupError,
    TableDropInProduction,
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


def test_delete_all_records(app):
    app.config["DEBUG"] = False

    with pytest.raises(RecordDeletionInProduction):
        delete_database(app)

    app.config["DEBUG"] = True


def test_drop_all_tables(app):
    app.config["DEBUG"] = False

    with pytest.raises(TableDropInProduction):
        drop_database(app)

    app.config["DEBUG"] = True
