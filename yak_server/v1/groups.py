from flask import Blueprint

from yak_server.database.models import GroupModel, PhaseModel

from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.flask_utils import success_response

groups = Blueprint("group", __name__)


@groups.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups")
@token_required
def get_groups(current_user):
    group_query = GroupModel.query.order_by(GroupModel.index)
    groups = [group.to_dict_with_phase_id() for group in group_query]

    phase_query = PhaseModel.query.order_by(PhaseModel.index)
    phases = [phase.to_dict() for phase in phase_query]

    return success_response(
        200,
        {
            "phases": phases,
            "groups": groups,
        },
    )


@groups.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/<string:group_code>")
@token_required
def get_group_by_code(current_user, group_code):
    group = GroupModel.query.filter_by(code=group_code).first()

    return success_response(
        200,
        {
            "phase": group.phase.to_dict(),
            "group": group.to_dict_without_phase(),
        },
    )


@groups.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/phases/<string:phase_code>")
@token_required
def get_groups_by_phase_code(current_user, phase_code):
    phase = PhaseModel.query.filter_by(code=phase_code).first()

    group_query = GroupModel.query.order_by(GroupModel.index).filter_by(phase_id=phase.id)
    groups = [group.to_dict_without_phase() for group in group_query]

    return success_response(
        200,
        {
            "phase": phase.to_dict(),
            "groups": groups,
        },
    )
