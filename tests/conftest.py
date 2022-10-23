import os

import pytest
from server import create_app
from server import db


@pytest.fixture(scope="session")
def app():
    # Override MYSQL_DB environment to push data to a different database
    os.environ["MYSQL_DB"] = "yak_toto_test"

    # Create app and set TESTING config
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )

    # Clean database before running test
    with app.app_context():
        db.drop_all()
        db.create_all()

    yield app

    # Clean database after running test
    with app.app_context():
        db.drop_all()


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()
