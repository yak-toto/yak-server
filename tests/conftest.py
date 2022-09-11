import pytest
from server import create_app
from server import db


@pytest.fixture
def app(monkeypatch):
    # Override MYSQL_DB environment to push data to a different database
    monkeypatch.setenv("MYSQL_DB", "yak_toto_test")

    # Create app and set TESTING config
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )

    # Clean database before running test
    db.drop_all(app=app)
    db.create_all(app=app)

    yield app

    # Clean database after running test
    db.drop_all(app=app)


@pytest.fixture
def client(app):
    return app.test_client()
