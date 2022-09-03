from flask import Blueprint
from flask import current_app

from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.errors import unauthorized_access_to_admin_api
from .utils.flask_utils import failed_response
from .utils.flask_utils import success_response

config = Blueprint("config", __name__)


@config.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/config")
@token_required
def config_get(current_user):
    if current_user.name != "admin":
        return failed_response(*unauthorized_access_to_admin_api)
    else:
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
            },
        )
