from typing import TYPE_CHECKING

from fastapi import status
from starlette.testclient import TestClient

if TYPE_CHECKING:
    from fastapi import FastAPI


def is_client_error(code: int) -> bool:
    return 400 <= code < 500


def is_server_error(code: int) -> bool:
    return 500 <= code < 600


def test_check_response_models(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    openapi_schema_response = client.get("/api/openapi.json")

    assert openapi_schema_response.status_code == status.HTTP_200_OK

    openapi_schema = openapi_schema_response.json()

    for path, item in openapi_schema["paths"].items():
        if path == "/api/health/":
            assert item["get"]["tags"] == ["health"]

            assert "200" in item["get"]["responses"]

            assert "503" in item["get"]["responses"]
            assert (
                item["get"]["responses"]["503"]["content"]["application/json"]["schema"]["$ref"]
                == "#/components/schemas/ErrorOut"
            )
            assert item["get"]["responses"]["503"]["description"] == "Service Unavailable"

        if path.startswith("/api/v1"):
            for specification in item.values():
                assert (
                    str(status.HTTP_200_OK) in specification["responses"]
                    or str(status.HTTP_201_CREATED) in specification["responses"]
                )

                assert str(status.HTTP_422_UNPROCESSABLE_CONTENT) in specification["responses"]

                for status_code, schema in specification["responses"].items():
                    if int(status_code) == status.HTTP_422_UNPROCESSABLE_CONTENT:
                        assert (
                            schema["content"]["application/json"]["schema"]["$ref"]
                            == "#/components/schemas/ValidationErrorOut"
                        )
                    elif is_client_error(int(status_code)) or is_server_error(int(status_code)):
                        assert (
                            schema["content"]["application/json"]["schema"]["$ref"]
                            == "#/components/schemas/ErrorOut"
                        )
