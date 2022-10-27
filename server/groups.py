from flask import Blueprint

from .models import Group
from .models import Phase
from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.flask_utils import success_response

groups = Blueprint("group", __name__)


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups")
@token_required
def get_groups(current_user):
    return success_response(
        200,
        [group.to_dict() for group in Group.query.order_by(Group.code)],
    )


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/<string:group_code>")
@token_required
def get_group_by_code(current_user, group_code):
    return success_response(
        200, Group.query.filter_by(code=group_code).first().to_dict()
    )


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/phases/<string:phase_code>")
@token_required
def get_groups_by_phase_code(current_user, phase_code):
    phase = Phase.query.filter_by(code=phase_code).first()

    return success_response(
        200,
        [
            group.to_dict()
            for group in Group.query.filter_by(phase_id=phase.id).order_by(Group.code)
        ],
    )
