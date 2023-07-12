from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from yak_server.config_file import get_settings

from .utils.mock import create_mock

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_no_schema_introspection_in_production(production_app: FastAPI) -> None:
    client = TestClient(production_app)

    production_app.dependency_overrides[get_settings] = create_mock()

    response = client.post(
        "/api/v2",
        json={
            "query": """{
                __schema {
                    queryType {
                        name
                    }
                }
            }
            """,
        },
    )

    assert response.json() == {
        "data": None,
        "errors": [
            {
                "message": (
                    "GraphQL introspection has been disabled, "
                    "but the requested query contained the field '__schema'."
                ),
                "locations": [
                    {
                        "line": 2,
                        "column": 17,
                    },
                ],
            },
            {
                "message": (
                    "GraphQL introspection has been disabled, "
                    "but the requested query contained the field 'queryType'."
                ),
                "locations": [
                    {
                        "line": 3,
                        "column": 21,
                    },
                ],
            },
        ],
    }
