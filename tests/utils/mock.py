import sys
from datetime import timedelta
from typing import TYPE_CHECKING, Dict

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources

from . import get_paris_datetime_now

if TYPE_CHECKING:
    from yak_server.config_file import RuleContainer


def create_mock(
    jwt_secret_key: str = None,
    jwt_expiration_time: int = None,
    data_folder: str = None,
    lock_datetime_shift: timedelta = None,
    rules: Dict[str, "RuleContainer"] = None,
    base_correct_result: int = None,
    multiplying_factor_correct_result: int = None,
    base_correct_score: int = None,
    multiplying_factor_correct_score: int = None,
    team_qualified: int = None,
    first_team_qualified: int = None,
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
            with resources.as_file(resources.files("tests") / "test_data" / data_folder) as path:
                mock.data_folder = path

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