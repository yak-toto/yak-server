import json
from pathlib import Path
from unittest.mock import Mock

import pkg_resources

from yak_server.cli import initialize_database

from .constants import HttpCode


def test_matches_db(app, client, monkeypatch):
    testcase = "test_matches_db"

    # location of test data
    app.config["DATA_FOLDER"] = pkg_resources.resource_filename(__name__, testcase)

    return_data = [
        "8f781aac-b29b-47e7-b6d7-06dd5e4859bb",
        "a963e889-57be-4c38-b65d-e28f196f7921",
        "b3f0f726-f3a5-4d5d-a22b-832d0ec2f36d",
        "7b6b14b8-0f4a-478f-b142-553ebcc0443f",
        "f5836ce2-03ce-42dd-a933-d93d9bb05441",
        "fdd9f52e-b6b6-4b6a-9737-4ec8165d3e0e",
        "a7c278ed-44e1-4ff8-9b5f-ba4751ffd39a",
        "632c2b94-d9d3-4583-9fd3-3d3d3711534e",
        "7dbf2941-4718-40cb-a8e9-d4baca79eca9",
        "2aa3e781-c9fe-44ae-ada7-25fd20430985",
        "d08ee014-36e9-44bc-9f3d-6d9bb0f9a9d1",
        "a7e02684-e8cc-4069-81c7-2ad44f2de747",
        "aed5723d-3102-4a63-b9f8-fe89c9685f44",
        "378c104b-4583-4f25-951e-78877f841132",
        "b39c3993-2795-41cb-91c1-34086c9b3684",
        "65c7c636-8907-404e-8341-1328f46e7c22",
        "16cbe0e8-e276-4f01-a0b6-09e0b352886c",
        "11ecc5a8-c5df-4dba-8094-f431be35c897",
        "3613762b-44d6-416f-a7c7-4055358bbcbf",
    ]

    test_mock = Mock(side_effect=return_data)
    monkeypatch.setattr("uuid.uuid4", test_mock)

    # initialize sql database
    initialize_database(app)

    client.post(
        "/api/v1/users/signup",
        json={
            "name": "clepape",
            "first_name": "admin",
            "last_name": "admin",
            "password": "clacla97",
        },
    )

    response_login = client.post(
        "/api/v1/users/login",
        json={
            "name": "clepape",
            "password": "clacla97",
        },
    )

    auth_token = response_login.json["result"]["token"]

    match_response = client.get(
        "/api/v1/matches",
        headers=[("Authorization", f"Bearer {auth_token}")],
    )

    with Path(
        pkg_resources.resource_filename(__name__, f"{testcase}/match_result.json"),
    ).open() as file:
        match_result = json.loads(file.read())

    assert match_response.status_code == HttpCode.OK
    assert match_response.json["result"] == match_result

    group_response = client.get(
        "/api/v1/groups/phases/GROUP",
        headers=[("Authorization", f"Bearer {auth_token}")],
    )

    with Path(
        pkg_resources.resource_filename(__name__, f"{testcase}/group_result.json"),
    ).open() as file:
        group_result = json.loads(file.read())

    assert group_response.status_code == HttpCode.OK
    assert group_response.json["result"] == group_result

    team_response = client.get("/api/v1/teams")

    with Path(
        pkg_resources.resource_filename(__name__, f"{testcase}/team_result.json"),
    ).open() as file:
        team_result = json.loads(file.read())

    assert team_response.status_code == HttpCode.OK
    assert team_response.json["result"] == team_result
