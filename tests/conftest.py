import os
from collections.abc import Generator
from typing import TYPE_CHECKING

import pendulum
import pymysql
import pytest
from fastapi.testclient import TestClient

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server import create_app
from yak_server.cli.database import create_database, delete_database, drop_database
from yak_server.database import get_mysql_settings
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI


def pytest_configure() -> None:
    mysql_settings = get_mysql_settings()

    connection = pymysql.connect(
        host=mysql_settings.host,
        user=mysql_settings.user_name,
        password=mysql_settings.password,
        port=mysql_settings.port,
    )

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {mysql_settings.db}")

        connection.commit()


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


@pytest.fixture
def production_app() -> "FastAPI":
    os.environ["DEBUG"] = "0"

    return create_app()


@pytest.fixture
def debug_app_with_profiler() -> Generator["FastAPI", None, None]:
    os.environ["PROFILING"] = "1"
    os.environ["DEBUG"] = "1"
    app = create_app()

    app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=10,
        jwt_secret_key=get_random_string(15),
        lock_datetime_shift=pendulum.duration(minutes=10),
    )

    # Clean database before running test
    create_database()

    yield app

    app.dependency_overrides = {}


@pytest.fixture
def production_app_with_profiler() -> Generator["FastAPI", None, None]:
    os.environ["PROFILING"] = "1"
    os.environ["DEBUG"] = "0"
    app = create_app()

    app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=10,
        jwt_secret_key=get_random_string(15),
        lock_datetime_shift=pendulum.duration(minutes=10),
    )

    # Clean database before running test
    create_database()

    yield app

    app.dependency_overrides = {}


@pytest.fixture
def app_with_valid_jwt_config(app: "FastAPI") -> Generator["FastAPI", None, None]:
    fake_jwt_secret_key = get_random_string(15)

    app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=20,
        jwt_secret_key=fake_jwt_secret_key,
        lock_datetime_shift=pendulum.duration(minutes=10),
    )

    yield app

    app.dependency_overrides = {}


@pytest.fixture
def app_with_null_jwt_expiration_time(app: "FastAPI") -> Generator["FastAPI", None, None]:
    fake_jwt_secret_key = get_random_string(15)

    app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=0,
        jwt_secret_key=fake_jwt_secret_key,
        lock_datetime_shift=pendulum.duration(minutes=10),
    )

    yield app

    app.dependency_overrides = {}


@pytest.fixture
def app_with_lock_datetime_in_past(app: "FastAPI") -> Generator["FastAPI", None, None]:
    fake_jwt_secret_key = get_random_string(15)

    app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=10,
        jwt_secret_key=fake_jwt_secret_key,
        lock_datetime_shift=pendulum.duration(seconds=-10),
    )

    yield app

    app.dependency_overrides = {}
