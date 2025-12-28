from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.testclient import TestClient

from testing.mock import MockSettings
from yak_server.helpers.settings import CompetitionSettings, get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_competition(app_with_valid_jwt_config: "FastAPI") -> None:
    app_with_valid_jwt_config.dependency_overrides[get_settings] = MockSettings(
        data_folder_relative="test_competition_v1",
        competition="WORLD_CUP_2026",
        competition_settings=CompetitionSettings(
            description_fr="Coupe du monde 2026",
            description_en="World Cup 2026",
        ),
    )

    client = TestClient(app_with_valid_jwt_config)

    # Test with default language (fr)
    response_default = client.get("/api/v1/competition")

    assert response_default.status_code == HTTPStatus.OK
    assert response_default.json() == {
        "ok": True,
        "result": {
            "code": "WORLD_CUP_2026",
            "description": "Coupe du monde 2026",
            "logo": {"url": "/api/v1/competition/logo"},
        },
    }

    # Test with French language explicitly
    response_fr = client.get("/api/v1/competition?lang=fr")

    assert response_fr.status_code == HTTPStatus.OK
    assert response_fr.json()["result"]["description"] == "Coupe du monde 2026"

    # Test with English language
    response_en = client.get("/api/v1/competition?lang=en")

    assert response_en.status_code == HTTPStatus.OK
    assert response_en.json()["result"]["description"] == "World Cup 2026"

    # Test with unsupported language
    response_invalid_lang = client.get("/api/v1/competition?lang=de")

    assert response_invalid_lang.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response_invalid_lang.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNPROCESSABLE_ENTITY,
        "description": [{"field": "query -> lang", "error": "Input should be 'fr' or 'en'"}],
    }


def test_competition_logo(app_with_valid_jwt_config: "FastAPI") -> None:
    app_with_valid_jwt_config.dependency_overrides[get_settings] = MockSettings(
        data_folder_relative="test_competition_v1",
        competition="WORLD_CUP_2026",
        competition_settings=CompetitionSettings(
            description_fr="Coupe du monde 2026",
            description_en="World Cup 2026",
        ),
    )

    client = TestClient(app_with_valid_jwt_config)

    response_logo = client.get("/api/v1/competition/logo")

    assert response_logo.status_code == HTTPStatus.OK
    assert "svg" in response_logo.headers["content-type"]
