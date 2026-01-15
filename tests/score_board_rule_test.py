from typing import TYPE_CHECKING

import pytest

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.admin import create_admin
from yak_server.cli.score_board import ComputePointsRuleNotDefinedError, compute_score_board
from yak_server.helpers.rules import Rules
from yak_server.v1.helpers.errors import NoAdminUser

if TYPE_CHECKING:
    from sqlalchemy import Engine


def test_score_board_rule_not_defined(
    monkeypatch: pytest.MonkeyPatch, engine_for_test_with_delete: "Engine"
) -> None:
    monkeypatch.setattr("yak_server.cli.score_board.get_settings", MockSettings(rules=Rules()))

    password_admin = get_random_string(10)

    create_admin(password_admin, engine_for_test_with_delete)

    with pytest.raises(ComputePointsRuleNotDefinedError) as exception:
        compute_score_board(engine_for_test_with_delete)

    assert str(exception.value) == "Compute points rule is not defined."


def test_score_board_rule_admin_user_not_found(engine_for_test_with_delete: "Engine") -> None:
    with pytest.raises(NoAdminUser) as exception:
        compute_score_board(engine_for_test_with_delete)

    assert str(exception.value) == "401: No admin user found"
