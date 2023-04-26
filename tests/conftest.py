from datetime import timedelta
from typing import TYPE_CHECKING, Generator

import pytest
from starlette.testclient import TestClient

from yak_server import create_fast_api_app
from yak_server.cli.database import create_database, delete_database, drop_database
from yak_server.config_file import get_settings

from .utils import get_random_string
from .utils.mock import create_mock

if TYPE_CHECKING:
    from fastapi import FastAPI


@pytest.fixture(scope="session")
def app_session() -> Generator:
    # Create app and set TESTING config
    app = create_fast_api_app()
    app.debug = True

    # Clean database before running test
    create_database()

    yield app

    # Clean database after running test
    drop_database(app)


@pytest.fixture(scope="module")
def app(app_session) -> Generator:
    # Clean database before running test
    delete_database(app_session)

    yield app_session

    # Clean database after running test
    delete_database(app_session)


@pytest.fixture(scope="module")
def client(app: "FastAPI") -> TestClient:
    return TestClient(app)


@pytest.fixture()
def production_app(app: "FastAPI") -> Generator:
    debug = app.debug
    app.debug = False

    yield app

    app.debug = debug


@pytest.fixture()
def app_with_valid_jwt_config(app: "FastAPI"):
    fake_jwt_secret_key = get_random_string(15)

    app.dependency_overrides[get_settings] = create_mock(
        jwt_expiration_time=10,
        jwt_secret_key=fake_jwt_secret_key,
        lock_datetime_shift=timedelta(seconds=10),
    )

    yield app

    app.dependency_overrides = {}


@pytest.fixture()
def app_with_null_jwt_expiration_time(app: "FastAPI"):
    fake_jwt_secret_key = get_random_string(15)

    app.dependency_overrides[get_settings] = create_mock(
        jwt_expiration_time=0,
        jwt_secret_key=fake_jwt_secret_key,
        lock_datetime_shift=timedelta(seconds=10),
    )

    yield app

    app.dependency_overrides = {}


@pytest.fixture()
def app_with_lock_datetime_in_past(app: "FastAPI"):
    fake_jwt_secret_key = get_random_string(15)

    app.dependency_overrides[get_settings] = create_mock(
        jwt_expiration_time=10,
        jwt_secret_key=fake_jwt_secret_key,
        lock_datetime_shift=timedelta(seconds=-10),
    )

    yield app

    app.dependency_overrides = {}
