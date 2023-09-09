from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from . import get_paris_datetime_now

if TYPE_CHECKING:
    from yak_server.helpers.settings import Rules


@dataclass
class MockSettings:
    def __init__(
        self,
        *,
        jwt_secret_key: Optional[str] = None,
        jwt_expiration_time: Optional[int] = None,
        data_folder_relative: Optional[str] = None,
        lock_datetime_shift: Optional[timedelta] = None,
        rules: "Optional[Rules]" = None,
        base_correct_result: Optional[int] = None,
        multiplying_factor_correct_result: Optional[int] = None,
        base_correct_score: Optional[int] = None,
        multiplying_factor_correct_score: Optional[int] = None,
        team_qualified: Optional[int] = None,
        first_team_qualified: Optional[int] = None,
    ) -> None:
        self.jwt_secret_key = jwt_secret_key
        self.jwt_expiration_time = jwt_expiration_time

        self.data_folder = (
            Path(__file__).parents[1] / "test_data" / data_folder_relative
            if data_folder_relative is not None
            else None
        )

        self.lock_datetime = (
            get_paris_datetime_now() + lock_datetime_shift
            if lock_datetime_shift is not None
            else None
        )

        self.rules = rules
        self.base_correct_result = base_correct_result
        self.multiplying_factor_correct_result = multiplying_factor_correct_result
        self.base_correct_score = base_correct_score
        self.multiplying_factor_correct_score = multiplying_factor_correct_score
        self.team_qualified = team_qualified
        self.first_team_qualified = first_team_qualified


def create_mock(**kwargs) -> Callable[[], MockSettings]:
    def get_settings_mock() -> MockSettings:
        return MockSettings(**kwargs)

    return get_settings_mock
