import sys
from typing import TYPE_CHECKING, Optional

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from .util import get_resources_path

if TYPE_CHECKING:
    import pendulum

    from yak_server.helpers.rules import Rules


class MockSettings:
    def __init__(
        self,
        *,
        data_folder_relative: Optional[str] = None,
        rules: Optional["Rules"] = None,
        official_results_url: Optional[str] = None,
    ) -> None:
        self.data_folder = (
            get_resources_path(data_folder_relative) if data_folder_relative is not None else None
        )

        self.rules = rules
        self.official_results_url = official_results_url

    def __call__(self) -> Self:
        return self


class MockLockDatetime:
    def __init__(self, lock_datetime: "pendulum.DateTime") -> None:
        self.lock_datetime = lock_datetime

    def __call__(self) -> "pendulum.DateTime":
        return self.lock_datetime


class MockAuthenticationSettings:
    def __init__(
        self,
        jwt_secret_key: str,
        jwt_refresh_secret_key: str,
        jwt_expiration_time: int,
        jwt_refresh_expiration_time: int,
    ) -> None:
        self.jwt_secret_key = jwt_secret_key
        self.jwt_refresh_secret_key = jwt_refresh_secret_key
        self.jwt_expiration_time = jwt_expiration_time
        self.jwt_refresh_expiration_time = jwt_refresh_expiration_time

    def __call__(self) -> Self:
        return self
