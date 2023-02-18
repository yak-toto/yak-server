from operator import itemgetter
from unittest.mock import ANY

import pkg_resources

from yak_server.cli import initialize_database

from .constants import HttpCode
from .test_utils import get_random_string


def test_matches_db(app, client):
    testcase = "test_matches_db"

    # location of test data
    app.config["DATA_FOLDER"] = pkg_resources.resource_filename(__name__, testcase)

    # initialize sql database
    initialize_database(app)

    # Signup admin user
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
                "flag": {"url": "https://fake-team-flag_andorra.com"},
            },
            "team2": {
                "id": ANY,
                "code": "BR",
                "description": "Brazil",
                "flag": {"url": "https://fake-team-flag_brazil.com"},
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
                "flag": {"url": "https://fake-team-flag_burkina.com"},
            },
            "team2": {
                "id": ANY,
                "code": "GT",
                "description": "The Republic of Guatemala",
                "flag": {"url": "https://fake-team-flag_guatemala.com"},
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
                "flag": {"url": "https://fake-team-flag_andorra.com"},
            },
            "team2": {
                "id": ANY,
                "code": "BF",
                "description": "Burkina Faso",
                "flag": {"url": "https://fake-team-flag_burkina.com"},
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
                "flag": {"url": "https://fake-team-flag_brazil.com"},
            },
            "team2": {
                "id": ANY,
                "code": "GT",
                "description": "The Republic of Guatemala",
                "flag": {"url": "https://fake-team-flag_guatemala.com"},
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
                "flag": {"url": "https://fake-team-flag_andorra.com"},
            },
            "team2": {
                "id": ANY,
                "code": "GT",
                "description": "The Republic of Guatemala",
                "flag": {"url": "https://fake-team-flag_guatemala.com"},
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
                "flag": {"url": "https://fake-team-flag_brazil.com"},
            },
            "team2": {
                "id": ANY,
                "code": "BF",
                "description": "Burkina Faso",
                "flag": {"url": "https://fake-team-flag_burkina.com"},
            },
        },
    ]

    match_response = client.get(
        "/api/v1/matches",
        headers=[("Authorization", f"Bearer {auth_token}")],
    )

    assert match_response.status_code == HttpCode.OK
    assert match_response.json["result"] == {
        "phases": [expected_phase],
        "groups": [expected_group],
        "matches": expected_matches,
    }

    # Check groups associated to one phase
    group_response = client.get(
        "/api/v1/groups/phases/GROUP",
        headers=[("Authorization", f"Bearer {auth_token}")],
    )

    assert group_response.status_code == HttpCode.OK
    assert group_response.json["result"] == {
        "phase": expected_phase,
        "groups": [expected_group_without_phase],
    }

    # Check all teams response
    team_response = client.get("/api/v1/teams")

    expected_teams = []

    for match in expected_matches:
        if match["team1"]["code"] not in [team["code"] for team in expected_teams]:
            expected_teams.append(match["team1"])

        if match["team2"]["code"] not in [team["code"] for team in expected_teams]:
            expected_teams.append(match["team2"])

    assert team_response.status_code == HttpCode.OK
    assert sorted(team_response.json["result"]["teams"], key=itemgetter("code")) == sorted(
        expected_teams,
        key=itemgetter("code"),
    )

    # Check GET /groups/{group_code}
    one_group_response = client.get(
        "/api/v1/groups/A",
        headers=[("Authorization", f"Bearer {auth_token}")],
    )

    assert one_group_response.status_code == 200
    assert one_group_response.json["result"] == {
        "group": expected_group_without_phase,
        "phase": expected_phase,
    }

    # Check GET /groups
    all_groups_response = client.get(
        "/api/v1/groups",
        headers=[("Authorization", f"Bearer {auth_token}")],
    )

    assert all_groups_response.status_code == 200
    assert all_groups_response.json["result"] == {
        "phases": [expected_phase],
        "groups": [expected_group],
    }
