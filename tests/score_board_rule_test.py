import pytest

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.database import (
    ComputePointsRuleNotDefinedError,
    compute_score_board,
    create_admin,
)
from yak_server.helpers.rules import Rules


def test_score_board_rule_not_defined(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("yak_server.cli.database.get_settings", MockSettings(rules=Rules()))

    password_admin = get_random_string(10)

    create_admin(password_admin)

    with pytest.raises(ComputePointsRuleNotDefinedError) as exception:
        compute_score_board()

    assert str(exception.value) == "Compute points rule is not defined."
