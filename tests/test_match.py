from http import HTTPStatus
from importlib import resources
from operator import itemgetter
from unittest.mock import ANY
from uuid import uuid4

from yak_server.cli.database import initialize_database

from .test_utils import get_random_string


def test_matches_db(app, client):
    testcase = "test_matches_db"

    # location of test data
    with resources.as_file(resources.files("tests") / testcase) as path:
        app.config["DATA_FOLDER"] = path

    # initialize sql database
    with app.app_context():
        initialize_database(app)

    # Signup one random user
    user_name = get_random_string(6)
    first_name = get_random_string(10)
    last_name = get_random_string(8)
    password = get_random_string(5)

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": user_name,
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
        },
    )

    auth_token = response_signup.json["result"]["token"]

    # Check all GET matches response
    expected_group = {"id": ANY, "code": "A", "phase": {"id": ANY}, "description": "Groupe A"}

    expected_group_without_phase = {
        key: value for key, value in expected_group.items() if key != "phase"
    }

    expected_phase = {
        "code": "GROUP",
        "description": "Group stage",
        "id": ANY,
    }

    expected_matches = [
        {
            "id": ANY,
            "index": 1,
            "group": {"id": ANY},
            "team1": {
                "id": ANY,
                "code": "AD",
                "description": "Andorra",
                "flag": {"url": ANY},
            },
            "team2": {
                "id": ANY,
                "code": "BR",
                "description": "Brazil",
                "flag": {"url": ANY},
            },
        },
        {
            "id": ANY,
            "index": 2,
            "group": {"id": ANY},
            "team1": {
                "id": ANY,
                "code": "BF",
                "description": "Burkina Faso",
                "flag": {"url": ANY},
            },
            "team2": {
                "id": ANY,
                "code": "GT",
                "description": "The Republic of Guatemala",
                "flag": {"url": ANY},
            },
        },
        {
            "id": ANY,
            "index": 3,
            "group": {"id": ANY},
            "team1": {
                "id": ANY,
                "code": "AD",
                "description": "Andorra",
                "flag": {"url": ANY},
            },
            "team2": {
                "id": ANY,
                "code": "BF",
                "description": "Burkina Faso",
                "flag": {"url": ANY},
            },
        },
        {
            "id": ANY,
            "index": 4,
            "group": {"id": ANY},
            "team1": {
                "id": ANY,
                "code": "BR",
                "description": "Brazil",
                "flag": {"url": ANY},
            },
            "team2": {
                "id": ANY,
                "code": "GT",
                "description": "The Republic of Guatemala",
                "flag": {"url": ANY},
            },
        },
        {
            "id": ANY,
            "index": 5,
            "group": {"id": ANY},
            "team1": {
                "id": ANY,
                "code": "AD",
                "description": "Andorra",
                "flag": {"url": ANY},
            },
            "team2": {
                "id": ANY,
                "code": "GT",
                "description": "The Republic of Guatemala",
                "flag": {"url": ANY},
            },
        },
        {
            "id": ANY,
            "index": 6,
            "group": {"id": ANY},
            "team1": {
                "id": ANY,
                "code": "BR",
                "description": "Brazil",
                "flag": {"url": ANY},
            },
            "team2": {
                "id": ANY,
                "code": "BF",
                "description": "Burkina Faso",
                "flag": {"url": ANY},
            },
        },
    ]

    all_matches_response = client.get(
        "/api/v1/matches",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert all_matches_response.status_code == HTTPStatus.OK
    assert all_matches_response.json["result"] == {
        "phases": [expected_phase],
        "groups": [expected_group],
        "matches": expected_matches,
    }

    match_id = all_matches_response.json["result"]["matches"][0]["id"]

    # Check GET matches/{matchId} with existing id
    match_response = client.get(
        f"/api/v1/matches/{match_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert match_response.status_code == HTTPStatus.OK
    assert match_response.json["result"]["match"] == {
        key: value for key, value in expected_matches[0].items() if key != "group"
    }

    # Check GET matches/{matchId} with non existing id
    invalid_match_id = str(uuid4())

    match_response_invalid_id = client.get(
        f"/api/v1/matches/{invalid_match_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert match_response_invalid_id.status_code == HTTPStatus.NOT_FOUND
    assert match_response_invalid_id.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Match not found: {invalid_match_id}",
    }

    # Check GET matches/phases/{phaseCode} with existing phase code
    matches_by_phase_code = client.get(
        "/api/v1/matches/phases/GROUP",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert matches_by_phase_code.status_code == HTTPStatus.OK
    assert matches_by_phase_code.json["result"] == {
        "phase": expected_phase,
        "groups": [expected_group_without_phase],
        "matches": expected_matches,
    }

    # Check GET matches/phases/{phaseCode} with non existing phase code
    invalid_phase_code = "GROUP1"

    matches_by_invalid_phase_code = client.get(
        f"/api/v1/matches/phases/{invalid_phase_code}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert matches_by_invalid_phase_code.status_code == HTTPStatus.NOT_FOUND
    assert matches_by_invalid_phase_code.json == {
        "ok": False,
        "description": f"Phase not found: {invalid_phase_code}",
        "error_code": HTTPStatus.NOT_FOUND,
    }

    # Check GET matches/groups/{groupCode} with existing code
    match_response_from_group_code = client.get(
        "/api/v1/matches/groups/A",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert match_response_from_group_code.json["result"]["matches"] == [
        {key: value for key, value in match.items() if key != "group"} for match in expected_matches
    ]

    # Check GET matches/groups/{groupCode} with non existing code
    invalid_group_code = "H"

    match_response_with_invalid_group_code = client.get(
        f"/api/v1/matches/groups/{invalid_group_code}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert match_response_with_invalid_group_code.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Group not found: {invalid_group_code}",
    }

    # Check all teams response
    team_response = client.get("/api/v1/teams")

    expected_teams = []

    for match in expected_matches:
        if match["team1"]["code"] not in [team["code"] for team in expected_teams]:
            expected_teams.append(match["team1"])

        if match["team2"]["code"] not in [team["code"] for team in expected_teams]:
            expected_teams.append(match["team2"])

    assert team_response.status_code == HTTPStatus.OK
    assert sorted(team_response.json["result"]["teams"], key=itemgetter("code")) == sorted(
        expected_teams,
        key=itemgetter("code"),
    )
