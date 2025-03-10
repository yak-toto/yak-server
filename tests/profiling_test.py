from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from scripts.profiling import create_app as create_app_with_profiler
from testing.util import get_random_string

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_debug_profiling(app_with_profiler: "FastAPI") -> None:
    client = TestClient(app_with_profiler)

    user_name = get_random_string(6)

    # Check signup is ok with profiling
    response = client.post(
        "/api/v1/users/signup",
        json={
            "name": user_name,
            "first_name": get_random_string(10),
            "last_name": get_random_string(12),
            "password": get_random_string(18),
        },
    )

    assert response.status_code == HTTPStatus.CREATED
    assert "profiling-log-id" in response.headers

    file_name = response.headers["profiling-log-id"]

    profiling_file = Path(__file__).parents[1] / "profiling" / f"{file_name}.pstats"
    assert profiling_file.exists()


def test_profiling_without_yappi_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("scripts.profiling.yappi", None)

    with pytest.raises(NotImplementedError) as exception:
        create_app_with_profiler()

    assert str(exception.value) == "Profiling is not available without yappi installed."
