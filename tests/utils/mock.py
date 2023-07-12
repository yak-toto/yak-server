from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from . import get_paris_datetime_now

if TYPE_CHECKING:
    from datetime import timedelta

    from yak_server.config_file import Rules


def create_mock(
    jwt_secret_key: str | None = None,
    jwt_expiration_time: int | None = None,
    data_folder: str | None = None,
    lock_datetime_shift: timedelta | None = None,
    rules: Rules | None = None,
    base_correct_result: int | None = None,
    multiplying_factor_correct_result: int | None = None,
    base_correct_score: int | None = None,
    multiplying_factor_correct_score: int | None = None,
    team_qualified: int | None = None,
    first_team_qualified: int | None = None,
):
    def mock_function():
        class Mock:
            pass

        mock = Mock()

        if jwt_secret_key is not None:
            mock.jwt_secret_key = jwt_secret_key

        if jwt_expiration_time is not None:
            mock.jwt_expiration_time = jwt_expiration_time

        if data_folder is not None:
            mock.data_folder = Path(__file__).parents[1] / "test_data" / data_folder

        if lock_datetime_shift is not None:
            mock.lock_datetime = get_paris_datetime_now() + lock_datetime_shift

        if rules is not None:
            mock.rules = rules

        if base_correct_result is not None:
            mock.base_correct_result = base_correct_result

        if multiplying_factor_correct_result is not None:
            mock.multiplying_factor_correct_result = multiplying_factor_correct_result

        if base_correct_score is not None:
            mock.base_correct_score = base_correct_score

        if multiplying_factor_correct_score is not None:
            mock.multiplying_factor_correct_score = multiplying_factor_correct_score

        if team_qualified is not None:
            mock.team_qualified = team_qualified

        if first_team_qualified is not None:
            mock.first_team_qualified = first_team_qualified

        return mock

    return mock_function
