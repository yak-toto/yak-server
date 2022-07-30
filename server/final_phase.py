from flask import Blueprint

from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.flask_utils import success_response

final_phase = Blueprint("final_phase", __name__)


@final_phase.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/final_phase", methods=["POST"])
@token_required
def final_phase_post(current_user):
    return success_response(200, current_user.to_user_dict())


@final_phase.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/final_phase")
@token_required
def final_phase_get(current_user):
    return success_response(200, current_user.to_user_dict())


@final_phase.route(
    f"/{GLOBAL_ENDPOINT}/{VERSION}/final_phase/<string:match_id>", methods=["PATCH"]
)
@token_required
def final_phase_patch(current_user, match_id):
    return success_response(200, current_user.to_user_dict())
