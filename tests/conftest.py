import os

import pytest

from yak_server import create_app
from yak_server.cli.database import create_database, delete_database, drop_database


@pytest.fixture(scope="session")
def app_session():
    # Override MYSQL_DB environment to push data to a different database
    os.environ["MYSQL_DB"] = "yak_toto_test"

    # Create app and set TESTING config
    app = create_app()
    app.config["TESTING"] = True
    app.config["DEBUG"] = True

    # Clean database before running test
    with app.app_context():
        create_database(app)

    yield app

    # Clean database after running test
    with app.app_context():
        drop_database(app)


@pytest.fixture(scope="module")
def app(app_session):
    # Clean database before running test
    with app_session.app_context():
        delete_database(app_session)

    yield app_session

    # Clean database after running test
    with app_session.app_context():
        delete_database(app_session)


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


@pytest.fixture()
def production_app(app):
    debug = app.config["DEBUG"]
    app.config["DEBUG"] = False

    yield app

    app.config["DEBUG"] = debug
