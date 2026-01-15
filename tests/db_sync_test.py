from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient

from testing.mock import MockSettings
from testing.util import get_random_string, get_resources_path
from yak_server.cli import app as typer_app
from yak_server.cli.admin import create_admin
from yak_server.cli.database import initialize_database

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy import Engine

runner = CliRunner()


@dataclass
class CompetitionData:
    url: str
    folder: str
    excepted_score_bets: list[tuple[int | None, int | None]]
    excepted_binary_bets: list[bool | None]


euro_2024_data = CompetitionData(
    url="https://en.wikipedia.org/wiki/UEFA_Euro_2024",
    folder="euro_2024",
    excepted_score_bets=[
        (5, 1),
        (1, 3),
        (2, 0),
        (1, 1),
        (1, 1),
        (0, 1),
        (3, 0),
        (2, 1),
        (2, 2),
        (1, 0),
        (0, 1),
        (1, 1),
        (1, 1),
        (0, 1),
        (1, 1),
        (1, 1),
        (0, 0),
        (0, 0),
        (1, 2),
        (0, 1),
        (1, 3),
        (0, 0),
        (2, 3),
        (1, 1),
        (3, 0),
        (0, 1),
        (1, 2),
        (2, 0),
        (1, 1),
        (0, 0),
        (3, 1),
        (2, 1),
        (1, 1),
        (0, 3),
        (2, 0),
        (1, 2),
    ],
    excepted_binary_bets=[
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ],
)

world_cup_2022_data = CompetitionData(
    url="https://en.wikipedia.org/wiki/2022_FIFA_World_Cup",
    folder="world_cup_2022",
    excepted_score_bets=[
        (0, 2),
        (0, 2),
        (1, 3),
        (1, 1),
        (1, 2),
        (2, 0),
        (6, 2),
        (1, 1),
        (0, 2),
        (0, 0),
        (0, 3),
        (0, 1),
        (1, 2),
        (0, 0),
        (2, 0),
        (2, 0),
        (0, 2),
        (1, 2),
        (0, 0),
        (4, 1),
        (0, 1),
        (2, 1),
        (1, 0),
        (1, 0),
        (1, 2),
        (7, 0),
        (0, 1),
        (1, 1),
        (2, 1),
        (2, 4),
        (0, 0),
        (1, 0),
        (0, 2),
        (4, 1),
        (0, 0),
        (1, 2),
        (1, 0),
        (2, 0),
        (3, 3),
        (1, 0),
        (2, 3),
        (1, 0),
        (0, 0),
        (3, 2),
        (2, 3),
        (2, 0),
        (0, 2),
        (2, 1),
    ],
    excepted_binary_bets=[
        True,
        True,
        True,
        True,
        False,
        True,
        True,
        True,
        True,
        False,
        True,
        False,
        True,
        True,
        True,
    ],
)

euro_2020_data = CompetitionData(
    url="https://en.wikipedia.org/wiki/UEFA_Euro_2020",
    folder="euro_2020",
    excepted_score_bets=[
        (0, 3),
        (1, 1),
        (0, 2),
        (3, 0),
        (3, 1),
        (1, 0),
        (0, 1),
        (3, 0),
        (0, 1),
        (1, 2),
        (1, 4),
        (0, 2),
        (3, 1),
        (3, 2),
        (2, 1),
        (2, 0),
        (0, 3),
        (0, 1),
        (1, 0),
        (0, 2),
        (1, 1),
        (0, 0),
        (3, 1),
        (0, 1),
        (1, 2),
        (0, 0),
        (1, 0),
        (1, 1),
        (0, 5),
        (3, 2),
        (0, 3),
        (1, 0),
        (1, 1),
        (2, 4),
        (2, 2),
        (2, 2),
    ],
    excepted_binary_bets=[
        False,
        True,
        False,
        True,
        False,
        False,
        True,
        False,
        False,
        False,
        False,
        False,
        True,
        True,
        True,
    ],
)

world_cup_2018_data = CompetitionData(
    url="https://en.wikipedia.org/wiki/2018_FIFA_World_Cup",
    folder="world_cup_2018",
    excepted_score_bets=[
        (5, 0),
        (0, 1),
        (3, 1),
        (1, 0),
        (3, 0),
        (2, 1),
        (0, 1),
        (3, 3),
        (1, 0),
        (0, 1),
        (1, 1),
        (2, 2),
        (2, 1),
        (0, 1),
        (1, 1),
        (1, 0),
        (0, 0),
        (0, 2),
        (1, 1),
        (2, 0),
        (0, 3),
        (2, 0),
        (1, 2),
        (1, 2),
        (0, 1),
        (1, 1),
        (2, 0),
        (1, 2),
        (0, 2),
        (2, 2),
        (0, 1),
        (1, 0),
        (1, 2),
        (2, 1),
        (2, 0),
        (0, 3),
        (3, 0),
        (1, 2),
        (5, 2),
        (6, 1),
        (0, 1),
        (1, 2),
        (1, 2),
        (1, 2),
        (2, 2),
        (0, 3),
        (0, 1),
        (0, 1),
    ],
    excepted_binary_bets=[
        True,
        True,
        False,
        True,
        True,
        True,
        True,
        False,
        False,
        False,
        False,
        False,
        True,
        True,
        True,
    ],
)

euro_2016_data = CompetitionData(
    url="https://en.wikipedia.org/wiki/UEFA_Euro_2016",
    folder="euro_2016",
    excepted_score_bets=[
        (2, 1),
        (0, 1),
        (1, 1),
        (2, 0),
        (0, 1),
        (0, 0),
        (2, 1),
        (1, 1),
        (1, 2),
        (2, 1),
        (0, 3),
        (0, 0),
        (1, 0),
        (2, 0),
        (0, 2),
        (0, 0),
        (0, 1),
        (0, 1),
        (0, 1),
        (1, 0),
        (2, 2),
        (3, 0),
        (0, 2),
        (2, 1),
        (1, 1),
        (0, 2),
        (1, 0),
        (3, 0),
        (0, 1),
        (0, 1),
        (0, 2),
        (1, 1),
        (1, 1),
        (0, 0),
        (2, 1),
        (3, 3),
    ],
    excepted_binary_bets=[
        False,
        True,
        False,
        True,
        True,
        False,
        True,
        False,
        False,
        True,
        True,
        True,
        True,
        False,
        True,
    ],
)


def idfn(value: CompetitionData) -> str:
    return value.folder


@pytest.mark.parametrize(
    "competition_data",
    [euro_2024_data, world_cup_2022_data, euro_2020_data, world_cup_2018_data, euro_2016_data],
    ids=idfn,
)
def test_db_sync(
    app_with_valid_jwt_config: "FastAPI",
    engine_for_test: "Engine",
    monkeypatch: "pytest.MonkeyPatch",
    competition_data: CompetitionData,
) -> None:
    # Setup fastapi application and initialize database
    initialize_database(
        engine_for_test,
        app_with_valid_jwt_config,
        get_resources_path(f"../../yak_server/data/{competition_data.folder}"),
    )

    # Signup admin user
    client = TestClient(app_with_valid_jwt_config)

    password = get_random_string(100)

    create_admin(password, engine_for_test)

    response_signup = client.post(
        "/api/v1/users/login",
        json={"name": "admin", "password": password},
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    access_token = response_signup.json()["result"]["access_token"]

    # Synchronize admin bets with official results
    monkeypatch.setattr(
        "yak_server.cli.get_settings",
        MockSettings(official_results_url=competition_data.url),
    )

    result = runner.invoke(typer_app, ["db", "sync"])

    assert result.exit_code == 0

    # Fetch all bets and check
    response_all_bets = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_all_bets.status_code == HTTPStatus.OK

    assert [
        (score_bet["team1"]["score"], score_bet["team2"]["score"])
        for score_bet in response_all_bets.json()["result"]["score_bets"]
    ] == competition_data.excepted_score_bets

    assert [
        binary_bet["team1"]["won"] if binary_bet["team1"] is not None else None
        for binary_bet in response_all_bets.json()["result"]["binary_bets"]
    ] == competition_data.excepted_binary_bets
