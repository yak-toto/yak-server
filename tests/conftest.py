import os

import pytest

from yak_server import create_app, db
from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    TeamModel,
    UserModel,
)


@pytest.fixture(scope="session")
def app_session():
    # Override MYSQL_DB environment to push data to a different database
    os.environ["MYSQL_DB"] = "yak_toto_test"

    # Create app and set TESTING config
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        },
    )

    # Clean database before running test
    with app.app_context():
        db.drop_all()
        db.create_all()

    yield app

    # Clean database after running test
    with app.app_context():
        db.drop_all()


@pytest.fixture(scope="module")
def app(app_session):
    # Clean database before running test
    with app_session.app_context():
        ScoreBetModel.query.delete()
        BinaryBetModel.query.delete()
        UserModel.query.delete()
        MatchModel.query.delete()
        GroupModel.query.delete()
        PhaseModel.query.delete()
        TeamModel.query.delete()
        db.session.commit()

    yield app_session

    # Clean database after running test
    with app_session.app_context():
        ScoreBetModel.query.delete()
        BinaryBetModel.query.delete()
        UserModel.query.delete()
        MatchModel.query.delete()
        GroupModel.query.delete()
        PhaseModel.query.delete()
        TeamModel.query.delete()
        db.session.commit()


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()
