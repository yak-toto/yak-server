import contextlib
import os
from collections.abc import Generator
from typing import TYPE_CHECKING

import pendulum
import psycopg2
import pytest
from fastapi.testclient import TestClient
from psycopg2 import sql

from scripts.profiling import create_app as create_app_with_profiling
from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server import create_app
from yak_server.cli.database import create_database, delete_database, drop_database
from yak_server.database import get_postgres_settings
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI


def pytest_configure() -> None:
    db_settings = get_postgres_settings()

    connection = psycopg2.connect(
        host=db_settings.host,
        user=db_settings.user_name,
        password=db_settings.password,
        port=db_settings.port,
        dbname="postgres",  # System database
    )
    connection.autocommit = True  # Required to create a database

    cursor = connection.cursor()

    with contextlib.suppress(psycopg2.errors.DuplicateDatabase):
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_settings.db)))

    cursor.close()
    connection.close()


@pytest.fixture(scope="session", autouse=True)
def app_session() -> Generator["FastAPI", None, None]:
    app = create_app()
    app.debug = True

    # Always drop database before running test session
    drop_database(app)

    # Always create database before running test session
    create_database()

    yield app

    # Always drop database atfer running test session
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
def app_with_profiler() -> Generator["FastAPI", None, None]:
    app = create_app_with_profiling()

    app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=100,
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
        jwt_expiration_time=100,
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
        jwt_expiration_time=100,
        jwt_secret_key=fake_jwt_secret_key,
        lock_datetime_shift=pendulum.duration(seconds=-10),
    )

    yield app

    app.dependency_overrides = {}
