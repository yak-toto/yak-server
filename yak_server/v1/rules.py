from http import HTTPStatus
from typing import TYPE_CHECKING, Tuple

from flask import Blueprint, current_app

from yak_server.helpers.rules import RULE_MAPPING

from .utils.auth_utils import is_authentificated
from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import RuleNotFound
from .utils.flask_utils import success_response

if TYPE_CHECKING:
    from flask import Response


rules = Blueprint("rules", __name__)


@rules.post(f"/{GLOBAL_ENDPOINT}/{VERSION}/rules/<string:rule_id>")
@is_authentificated
def execute_rule(user, rule_id) -> Tuple["Response", int]:
    if rule_id not in current_app.config["RULES"]:
        raise RuleNotFound(rule_id)

    RULE_MAPPING[rule_id](user, current_app.config["RULES"][rule_id])

    return success_response(HTTPStatus.OK, None)
