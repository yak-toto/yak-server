from typing import TYPE_CHECKING

import pytest
from fastapi import status

if TYPE_CHECKING:
    from fastapi import FastAPI


def is_client_error(code: int) -> bool:
    return 400 <= code < 500


def is_server_error(code: int) -> bool:
    return 500 <= code < 600


def test_check_response_models(app_with_valid_jwt_config: "FastAPI") -> None:
    openapi_schema = app_with_valid_jwt_config.openapi()

    for path, item in openapi_schema["paths"].items():
        if path.startswith("/api/v1"):
            for method, specification in item.items():
                if (
                    str(status.HTTP_200_OK) not in specification["responses"]
                    and str(status.HTTP_201_CREATED) not in specification["responses"]
                ):
                    pytest.fail(f"Missing 200 or 201 response for {method} {path}")

                if str(status.HTTP_422_UNPROCESSABLE_ENTITY) not in specification["responses"]:
                    pytest.fail(f"Missing 422 response for {method} {path}")

                for status_code, schema in specification["responses"].items():
                    if is_client_error(int(status_code)) or is_server_error(int(status_code)):
                        assert schema["content"]["application/json"]["schema"]["$ref"] in {
                            "#/components/schemas/ErrorOut",
                            "#/components/schemas/HTTPValidationError",
                        }
