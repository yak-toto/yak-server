from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from .utils import get_random_string

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_debug_profiling(debug_app_with_profiler: "FastAPI") -> None:
    client = TestClient(debug_app_with_profiler)

    user_name = get_random_string(6)

    # Check signup is ok with profiling
    response = client.post(
        "/api/v1/users/signup",
        json={
            "name": user_name,
            "first_name": get_random_string(10),
            "last_name": get_random_string(12),
            "password": get_random_string(6),
        },
    )

    assert response.status_code == HTTPStatus.CREATED
    assert "profiling-log-id" in response.headers

    file_name = response.headers["profiling-log-id"]

    profiling_file = Path(__file__).parents[1] / "profiling" / f"{file_name}.pstats"
    assert profiling_file.exists()


def test_production_profiling(production_app_with_profiler: "FastAPI") -> None:
    client = TestClient(production_app_with_profiler)

    user_name = get_random_string(6)

    # Check signup is ok with profiling
    response = client.post(
        "/api/v1/users/signup",
        json={
            "name": user_name,
            "first_name": get_random_string(10),
            "last_name": get_random_string(12),
            "password": get_random_string(6),
        },
    )

    assert response.status_code == HTTPStatus.CREATED
    assert "profiling-log-id" not in response.headers
