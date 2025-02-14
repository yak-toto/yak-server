import contextlib
import os
from collections.abc import Generator
from typing import TYPE_CHECKING

import pendulum
import psycopg2
import pytest
from psycopg2 import sql
from sqlalchemy import Engine, create_engine

from scripts.profiling import create_app as create_app_with_profiling
from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server import create_app
from yak_server.cli.database import create_database, delete_database, drop_database
from yak_server.database import compute_database_uri, get_postgres_settings
from yak_server.helpers.rules import Rules
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI


def create_test_database() -> Engine:
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

    database_url = compute_database_uri(
        psycopg2.__name__,
        db_settings.host,
        db_settings.user_name,
        db_settings.password,
        db_settings.port,
        db_settings.db,
    )

    return create_engine(database_url, pool_recycle=7200, pool_pre_ping=True)


@pytest.fixture(scope="session", autouse=True)
def engine_for_test() -> Generator[Engine, None, None]:
    engine = create_test_database()

    # Always drop database before running test session
    drop_database(engine, debug=True)

    # Always create database before running test session
    create_database(engine)

    yield engine

    # Always drop database atfer running test session
    drop_database(engine, debug=True)


@pytest.fixture
def engine_for_test_with_delete(engine_for_test: Engine) -> Generator[Engine, None, None]:
    delete_database(engine_for_test, debug=True)

    yield engine_for_test

    delete_database(engine_for_test, debug=True)


@pytest.fixture(scope="session")
def _debug_app_session() -> "FastAPI":
    os.environ["DEBUG"] = "1"

    return create_app()


@pytest.fixture(scope="session")
def production_app_session() -> "FastAPI":
    os.environ["DEBUG"] = "0"

    return create_app()


@pytest.fixture
def _app(
    _debug_app_session: "FastAPI", engine_for_test: "Engine"
) -> Generator["FastAPI", None, None]:
    # Clean database before running test
    delete_database(engine_for_test, debug=True)

    yield _debug_app_session

    # Clean database after running test
    delete_database(engine_for_test, debug=True)


@pytest.fixture
def app_with_profiler() -> Generator["FastAPI", None, None]:
    os.environ["DEBUG"] = "1"

    app = create_app_with_profiling()

    app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=100,
        jwt_secret_key=get_random_string(15),
        lock_datetime_shift=pendulum.duration(minutes=10),
    )

    yield app

    app.dependency_overrides.clear()


@pytest.fixture
def app_with_valid_jwt_config(_app: "FastAPI") -> Generator["FastAPI", None, None]:
    _app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=100,
        jwt_secret_key=get_random_string(15),
        lock_datetime_shift=pendulum.duration(minutes=10),
    )

    yield _app

    _app.dependency_overrides.clear()


@pytest.fixture
def app_with_null_jwt_expiration_time(_app: "FastAPI") -> Generator["FastAPI", None, None]:
    _app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=0,
        jwt_secret_key=get_random_string(15),
        lock_datetime_shift=pendulum.duration(minutes=10),
    )

    yield _app

    _app.dependency_overrides.clear()


@pytest.fixture
def app_with_lock_datetime_in_past(_app: "FastAPI") -> Generator["FastAPI", None, None]:
    _app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=100,
        jwt_secret_key=get_random_string(15),
        lock_datetime_shift=pendulum.duration(seconds=-10),
    )

    yield _app

    _app.dependency_overrides.clear()


@pytest.fixture
def app_with_empty_rules(_app: "FastAPI") -> Generator["FastAPI", None, None]:
    _app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=100,
        jwt_secret_key=get_random_string(15),
        lock_datetime_shift=pendulum.duration(seconds=10),
        rules=Rules(),
    )

    yield _app

    _app.dependency_overrides.clear()
