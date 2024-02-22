from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from testing.mock import MockSettings
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_no_schema_introspection_in_production(production_app: "FastAPI") -> None:
    client = TestClient(production_app)

    production_app.dependency_overrides[get_settings] = MockSettings()

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
