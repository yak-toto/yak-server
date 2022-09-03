from operator import itemgetter

from flask import Blueprint
from sqlalchemy import or_

from .models import Group
from .models import Matches
from .models import Phase
from .models import Team
from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.errors import invalid_team_id
from .utils.errors import match_not_found
from .utils.errors import team_not_found
from .utils.errors import unauthorized_access_to_admin_api
from .utils.flask_utils import failed_response
from .utils.flask_utils import is_iso_3166_1_alpha_2_code
from .utils.flask_utils import is_uuid4
from .utils.flask_utils import success_response

groups = Blueprint("group", __name__)


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/names")
@token_required
def groups_names(current_user):
    phase = Phase.query.filter_by(code="GROUP").first()

    return success_response(
        200,
        [
            phase.to_dict()
            for phase in Group.query.filter_by(phase_id=phase.id).order_by(Group.code)
        ],
    )


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches")
@token_required
def matches(current_user):
    if current_user.name == "admin":
        return success_response(
            200,
            sorted(
                (match.to_dict() for match in Matches.query.all()),
                key=lambda match: (match["group"]["code"], match["index"]),
            ),
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


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches/groups/<string:group_name>")
@token_required
def matches_phases_get(current_user, group_name):
    group = Group.query.filter_by(code=group_name).first()

    return success_response(
        200,
        sorted(
            (match.to_dict() for match in Matches.query.filter_by(group_id=group.id)),
            key=itemgetter("index"),
        ),
    )


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches/teams/<string:team_id>")
@token_required
def matches_teams_get(current_user, team_id):
    if is_uuid4(team_id):
        team = Team.query.get(team_id)
    elif is_iso_3166_1_alpha_2_code(team_id):
        team = Team.query.filter_by(code=team_id).first()
    else:
        return failed_response(*invalid_team_id)

    if not team:
        return failed_response(*team_not_found)

    matches = Matches.query.filter(
        or_(Matches.team1_id == team.id, Matches.team2_id == team.id)
    )

    return success_response(200, [match.to_dict() for match in matches])
