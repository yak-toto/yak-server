from typing import TYPE_CHECKING

from yak_server.database.models import UserModel
from yak_server.database.session import build_local_session_maker
from yak_server.helpers.rules.compute_points import compute_points
from yak_server.helpers.settings import get_settings
from yak_server.v1.helpers.errors import NoAdminUser

if TYPE_CHECKING:
    from sqlalchemy import Engine


class ComputePointsRuleNotDefinedError(Exception):
    def __init__(self) -> None:
        super().__init__("Compute points rule is not defined.")


def compute_score_board(engine: "Engine") -> None:
    local_session_maker = build_local_session_maker(engine)

    with local_session_maker() as db:
        admin = db.query(UserModel).filter_by(name="admin").first()

        if admin is None:
            raise NoAdminUser

        rule_config = get_settings().rules.compute_points

        if rule_config is None:
            raise ComputePointsRuleNotDefinedError

        compute_points(db, admin, rule_config)
