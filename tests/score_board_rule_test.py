from typing import TYPE_CHECKING, cast

import pytest

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.admin import create_admin
from yak_server.cli.score_board import ComputePointsRuleNotDefinedError, compute_score_board
from yak_server.helpers.rules import Rules
from yak_server.v1.helpers.errors import NoAdminUser

if TYPE_CHECKING:
    from sqlalchemy import Engine

    from yak_server.helpers.settings import Settings


def test_score_board_rule_not_defined(engine_for_test_with_delete: "Engine") -> None:
    password_admin = get_random_string(10)

    create_admin(password_admin, engine_for_test_with_delete)

    with pytest.raises(ComputePointsRuleNotDefinedError) as exception:
        compute_score_board(
            engine_for_test_with_delete, cast("Settings", MockSettings(rules=Rules()))
        )

    assert str(exception.value) == "Compute points rule is not defined."


def test_score_board_rule_admin_user_not_found(engine_for_test_with_delete: "Engine") -> None:
    with pytest.raises(NoAdminUser) as exception:
        compute_score_board(
            engine_for_test_with_delete, cast("Settings", MockSettings(rules=Rules()))
        )

    assert str(exception.value) == "401: No admin user found"
