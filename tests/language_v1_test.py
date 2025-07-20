from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.testclient import TestClient

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.database import initialize_database

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI
    from sqlalchemy import Engine


def test_group(
    app_with_valid_jwt_config: "FastAPI",
    engine_for_test: "Engine",
    monkeypatch: "pytest.MonkeyPatch",
) -> None:
    client = TestClient(app_with_valid_jwt_config)

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_language"),
    )
    initialize_database(engine_for_test, app_with_valid_jwt_config)

    # Signup one random user
    user_name = get_random_string(6)
    first_name = get_random_string(10)
    last_name = get_random_string(8)
    password = get_random_string(9)

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": user_name,
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
        },
    )

    auth_token = response_signup.json()["result"]["access_token"]

    # retrieve all bets with default language
    response_default_lang = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response_default_lang.json()["result"]["phases"][0]["description"] == "Phase de groupes"
    assert response_default_lang.json()["result"]["groups"][0]["description"] == "Groupe A"
    assert response_default_lang.json()["result"]["score_bets"][0]["team1"]["description"] == "Laos"
    assert (
        response_default_lang.json()["result"]["score_bets"][0]["team2"]["description"]
        == "Thaïlande"
    )

    # retrieve all bets with french language
    response_french_lang = client.get(
        "/api/v1/bets?lang=fr",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert (
        response_default_lang.json()["result"]["phases"][0]["description"]
        == response_french_lang.json()["result"]["phases"][0]["description"]
    )
    assert (
        response_default_lang.json()["result"]["groups"][0]["description"]
        == response_french_lang.json()["result"]["groups"][0]["description"]
    )
    assert (
        response_default_lang.json()["result"]["score_bets"][0]["team1"]["description"]
        == response_french_lang.json()["result"]["score_bets"][0]["team1"]["description"]
    )
    assert (
        response_default_lang.json()["result"]["score_bets"][0]["team1"]["description"]
        == response_french_lang.json()["result"]["score_bets"][0]["team1"]["description"]
    )

    # retrieve all bets with english language
    response_english_lang = client.get(
        "/api/v1/bets?lang=en",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response_english_lang.json()["result"]["phases"][0]["description"] == "Group stage"
    assert response_english_lang.json()["result"]["groups"][0]["description"] == "Group A"
    assert response_english_lang.json()["result"]["score_bets"][0]["team1"]["description"] == "Laos"
    assert (
        response_english_lang.json()["result"]["score_bets"][0]["team2"]["description"]
        == "Thailand"
    )

    # retrieve all bets with unknown language
    response_german_lang = client.get(
        "/api/v1/bets?lang=de",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response_german_lang.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response_german_lang.json() == {
        "description": [{"field": "query -> lang", "error": "Input should be 'fr' or 'en'"}],
        "error_code": HTTPStatus.UNPROCESSABLE_ENTITY,
        "ok": False,
    }
