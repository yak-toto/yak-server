from flask import Blueprint, current_app

from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import UnauthorizedAccessToAdminAPI
from .utils.flask_utils import success_response

config = Blueprint("config", __name__)


@config.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/config")
@token_required
def config_get(current_user):
    if current_user.name != "admin":
        raise UnauthorizedAccessToAdminAPI

    return success_response(
        200,
        {
            "locked_datetime": current_app.config["LOCK_DATETIME"],
            "base_correct_result": current_app.config["BASE_CORRECT_RESULT"],
            "multiplying_factor_correct_result": current_app.config[
                "MULTIPLYING_FACTOR_CORRECT_RESULT"
            ],
            "base_correct_score": current_app.config["BASE_CORRECT_SCORE"],
            "multiplying_factor_correct_score": current_app.config[
                "MULTIPLYING_FACTOR_CORRECT_SCORE"
            ],
            "team_qualified": current_app.config["TEAM_QUALIFIED"],
            "first_team_qualified": current_app.config["FIRST_TEAM_QUALIFIED"],
        },
    )
