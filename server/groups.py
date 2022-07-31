from flask import Blueprint
from sqlalchemy import or_

from .models import Matches
from .models import Phase
from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.errors import match_not_found
from .utils.errors import unauthorized_access_to_admin_api
from .utils.flask_utils import failed_response
from .utils.flask_utils import success_response

groups = Blueprint("group", __name__)


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/names")
@token_required
def groups_names(current_user):
    return success_response(
        200,
        [
            phase.to_dict()
            for phase in Phase.query.filter_by(
                phase_description="Phase de groupe"
            ).order_by(Phase.code)
        ],
    )


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches")
@token_required
def matches(current_user):
    if current_user.name == "admin":
        return success_response(
            200,
            [
                match.to_dict()
                for match in Matches.query.order_by(
                    Matches.group_name, Matches.match_index
                )
            ],
        )

    else:
        return failed_response(*unauthorized_access_to_admin_api)


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches/<string:match_id>")
@token_required
def matches_get_by_id(current_user, match_id):
    if current_user.name in ("admin"):
        match = Matches.query.filter_by(id=match_id).first()

        if not match:
            return failed_response(*match_not_found)

        return success_response(200, match.to_dict())
    else:
        return failed_response(*unauthorized_access_to_admin_api)


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches/phases/<string:phase_name>")
@token_required
def matches_phases_get(current_user, phase_name):
    phase = Phase.query.filter_by(code=phase_name).first()

    return success_response(
        200, [match.to_dict() for match in Matches.query.filter_by(phase_id=phase.id)]
    )


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches/teams/<string:team_id>")
@token_required
def matches_teams_get(current_user, team_id):
    matches = Matches.query.filter(
        or_(Matches.team1_id == team_id, Matches.team2_id == team_id)
    )

    return success_response(200, [match.to_dict() for match in matches])
