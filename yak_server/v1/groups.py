from http import HTTPStatus
from typing import TYPE_CHECKING, Tuple

from flask import Blueprint

from yak_server.database.models import GroupModel, PhaseModel

from .utils.auth_utils import is_authentificated
from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import GroupNotFound, PhaseNotFound
from .utils.flask_utils import success_response

if TYPE_CHECKING:
    from flask import Response


groups = Blueprint("group", __name__)


@groups.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups")
@is_authentificated
def get_groups(current_user) -> Tuple["Response", int]:
    group_query = GroupModel.query.order_by(GroupModel.index)
    groups = [group.to_dict_with_phase_id() for group in group_query]

    phase_query = PhaseModel.query.order_by(PhaseModel.index)
    phases = [phase.to_dict() for phase in phase_query]

    return success_response(
        HTTPStatus.OK,
        {
            "phases": phases,
            "groups": groups,
        },
    )


@groups.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/<string:group_code>")
@is_authentificated
def get_group_by_code(current_user, group_code) -> Tuple["Response", int]:
    group = GroupModel.query.filter_by(code=group_code).first()

    if not group:
        raise GroupNotFound(group_code)

    return success_response(
        HTTPStatus.OK,
        {
            "phase": group.phase.to_dict(),
            "group": group.to_dict_without_phase(),
        },
    )


@groups.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/phases/<string:phase_code>")
@is_authentificated
def get_groups_by_phase_code(current_user, phase_code) -> Tuple["Response", int]:
    phase = PhaseModel.query.filter_by(code=phase_code).first()

    if not phase:
        raise PhaseNotFound(phase_code)

    group_query = GroupModel.query.order_by(GroupModel.index).filter_by(phase_id=phase.id)
    groups = [group.to_dict_without_phase() for group in group_query]

    return success_response(
        HTTPStatus.OK,
        {
            "phase": phase.to_dict(),
            "groups": groups,
        },
    )
