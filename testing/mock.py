from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

import pendulum

from .util import get_resources_path

if TYPE_CHECKING:
    from yak_server.helpers.rules import Rules


class MockSettings:
    def __init__(
        self,
        *,
        jwt_secret_key: str | None = None,
        jwt_expiration_time: int | None = None,
        data_folder_relative: str | None = None,
        lock_datetime_shift: pendulum.Duration | None = None,
        rules: Rules | None = None,
        base_correct_result: int | None = None,
        multiplying_factor_correct_result: int | None = None,
        base_correct_score: int | None = None,
        multiplying_factor_correct_score: int | None = None,
        team_qualified: int | None = None,
        first_team_qualified: int | None = None,
        official_results_url: str | None = None,
    ) -> None:
        self.jwt_secret_key = jwt_secret_key
        self.jwt_expiration_time = jwt_expiration_time

        self.data_folder = (
            get_resources_path(data_folder_relative) if data_folder_relative is not None else None
        )

        self.lock_datetime = (
            pendulum.now() + lock_datetime_shift if lock_datetime_shift is not None else None
        )

        self.rules = rules
        self.base_correct_result = base_correct_result
        self.multiplying_factor_correct_result = multiplying_factor_correct_result
        self.base_correct_score = base_correct_score
        self.multiplying_factor_correct_score = multiplying_factor_correct_score
        self.team_qualified = team_qualified
        self.first_team_qualified = first_team_qualified
        self.official_results_url = official_results_url

    def __call__(self) -> Self:
        return self
