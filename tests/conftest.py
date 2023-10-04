import os
from typing import TYPE_CHECKING, Generator

import pendulum
import pytest
from starlette.testclient import TestClient

from yak_server import create_app
from yak_server.cli.database import create_database, delete_database, drop_database
from yak_server.helpers.settings import get_settings

from .utils import get_random_string
from .utils.mock import create_mock

if TYPE_CHECKING:
    from fastapi import FastAPI


@pytest.fixture(scope="session")
def app_session() -> Generator["FastAPI", None, None]:
    # Create app and set TESTING config
    app = create_app()
    app.debug = True

    # Clean database before running test
    create_database()

    yield app

    # Clean database after running test
    drop_database(app)


@pytest.fixture(scope="module")
def app(app_session: "FastAPI") -> Generator["FastAPI", None, None]:
    # Clean database before running test
    delete_database(app_session)

    yield app_session

    # Clean database after running test
    delete_database(app_session)


@pytest.fixture(scope="module")
def client(app: "FastAPI") -> TestClient:
    return TestClient(app)


@pytest.fixture()
def production_app() -> "FastAPI":
    os.environ["DEBUG"] = "0"

    return create_app()


@pytest.fixture()
def debug_app_with_profiler() -> Generator["FastAPI", None, None]:
    os.environ["PROFILING"] = "1"
    os.environ["DEBUG"] = "1"
    app = create_app()

    app.dependency_overrides[get_settings] = create_mock(
        jwt_expiration_time=10,
        jwt_secret_key=get_random_string(15),
        lock_datetime_shift=pendulum.duration(seconds=10),
    )

    # Clean database before running test
    create_database()

    yield app

    app.dependency_overrides = {}


@pytest.fixture()
def production_app_with_profiler() -> Generator["FastAPI", None, None]:
    os.environ["PROFILING"] = "1"
    os.environ["DEBUG"] = "0"
    app = create_app()

    app.dependency_overrides[get_settings] = create_mock(
        jwt_expiration_time=10,
        jwt_secret_key=get_random_string(15),
        lock_datetime_shift=pendulum.duration(seconds=10),
    )

    # Clean database before running test
    create_database()

    yield app

    app.dependency_overrides = {}


@pytest.fixture()
def app_with_valid_jwt_config(app: "FastAPI") -> Generator["FastAPI", None, None]:
    fake_jwt_secret_key = get_random_string(15)

    app.dependency_overrides[get_settings] = create_mock(
        jwt_expiration_time=10,
        jwt_secret_key=fake_jwt_secret_key,
        lock_datetime_shift=pendulum.duration(seconds=10),
    )

    yield app

    app.dependency_overrides = {}


@pytest.fixture()
def app_with_null_jwt_expiration_time(app: "FastAPI") -> Generator["FastAPI", None, None]:
    fake_jwt_secret_key = get_random_string(15)

    app.dependency_overrides[get_settings] = create_mock(
        jwt_expiration_time=0,
        jwt_secret_key=fake_jwt_secret_key,
        lock_datetime_shift=pendulum.duration(seconds=10),
    )

    yield app

    app.dependency_overrides = {}


@pytest.fixture()
def app_with_lock_datetime_in_past(app: "FastAPI") -> Generator["FastAPI", None, None]:
    fake_jwt_secret_key = get_random_string(15)

    app.dependency_overrides[get_settings] = create_mock(
        jwt_expiration_time=10,
        jwt_secret_key=fake_jwt_secret_key,
        lock_datetime_shift=pendulum.duration(seconds=-10),
    )

    yield app

    app.dependency_overrides = {}
