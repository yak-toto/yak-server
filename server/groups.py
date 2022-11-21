from flask import Blueprint
from sqlalchemy import desc

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
    group_query = Group.query.join(Group.phase).order_by(desc(Phase.code), Group.code)
    groups = [group.to_dict_with_phase_id() for group in group_query]

    phase_query = Phase.query.order_by(desc(Phase.code))
    phases = [phase.to_dict() for phase in phase_query]

    return success_response(
        200,
        {
            "phases": phases,
            "groups": groups,
        },
    )


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/<string:group_code>")
@token_required
def get_group_by_code(current_user, group_code):
    group = Group.query.filter_by(code=group_code).first()

    return success_response(
        200,
        {
            "phase": group.phase.to_dict(),
            "group": group.to_dict_without_phase(),
        },
    )


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/phases/<string:phase_code>")
@token_required
def get_groups_by_phase_code(current_user, phase_code):
    phase = Phase.query.filter_by(code=phase_code).first()

    group_query = Group.query.order_by(Group.code).filter_by(phase_id=phase.id)
    groups = [group.to_dict_without_phase() for group in group_query]

    return success_response(
        200,
        {
            "phase": phase.to_dict(),
            "groups": groups,
        },
    )
