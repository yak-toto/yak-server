from http import HTTPStatus
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.testclient import TestClient


def test_endpoint_not_found(client: "TestClient") -> None:
    response = client.get("/api/v1/fffffff")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": "Not Found",
    }
