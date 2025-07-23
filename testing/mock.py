import sys
from typing import TYPE_CHECKING, Optional

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

import pendulum

from .util import get_resources_path

if TYPE_CHECKING:
    from yak_server.helpers.rules import Rules


class MockSettings:
    def __init__(  # noqa: PLR0913
        self,
        *,
        jwt_secret_key: Optional[str] = None,
        jwt_expiration_time: Optional[int] = None,
        jwt_refresh_expiration_time: Optional[int] = None,
        data_folder_relative: Optional[str] = None,
        lock_datetime_shift: Optional[pendulum.Duration] = None,
        rules: Optional["Rules"] = None,
        official_results_url: Optional[str] = None,
    ) -> None:
        self.jwt_secret_key = jwt_secret_key
        self.jwt_expiration_time = jwt_expiration_time
        self.jwt_refresh_expiration_time = jwt_refresh_expiration_time

        self.data_folder = (
            get_resources_path(data_folder_relative) if data_folder_relative is not None else None
        )

        self.lock_datetime = (
            pendulum.now() + lock_datetime_shift if lock_datetime_shift is not None else None
        )

        self.rules = rules
        self.official_results_url = official_results_url

    def set_lock_datetime(self, lock_datetime_shift: pendulum.Duration) -> None:
        self.lock_datetime = pendulum.now() + lock_datetime_shift

    def __call__(self) -> Self:
        return self
