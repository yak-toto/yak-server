from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.testclient import TestClient

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_endpoint_not_found(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    response = client.get("/api/v1/fffffff")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": "Not Found",
    }
