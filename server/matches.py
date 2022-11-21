from flask import Blueprint
from flask import request
from sqlalchemy import desc
from sqlalchemy import or_

from . import db
from .models import Group
from .models import Match
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

matches = Blueprint("matches", __name__)


@matches.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches", methods=["POST"])
@token_required
def match_post(current_user):
    if current_user.name == "admin":
        body = request.get_json()

        match = Match(
            group_id=body["group"]["id"],
            team1_id=body["team1"]["id"],
            team2_id=body["team2"]["id"],
            index=body["index"],
        )

        db.session.add(match)
        db.session.commit()

        group = Group.query.filter_by(id=match.group_id).first()

        return success_response(
            200,
            {
                "phase": group.phase.to_dict(),
                "group": group.to_dict_without_phase(),
                "match": match.to_dict_without_group(),
            },
        )
    else:
        return failed_response(*unauthorized_access_to_admin_api)


@matches.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches")
@token_required
def matches_get_all(current_user):
    match_query = (
        Match.query.join(Match.group)
        .join(Group.phase)
        .order_by(desc(Phase.code), Group.code, Match.index)
    )
    matches = [match.to_dict_with_group_id() for match in match_query]

    group_query = Group.query.join(Group.phase).order_by(desc(Phase.code), Group.code)
    groups = [group.to_dict_with_phase_id() for group in group_query]

    phase_query = Phase.query.order_by(desc(Phase.code))
    phases = [phase.to_dict() for phase in phase_query]

    return success_response(
        200,
        {
            "phases": phases,
            "groups": groups,
            "matches": matches,
        },
    )


@matches.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches/<string:match_id>")
@token_required
def matches_get_by_id(current_user, match_id):
    match = Match.query.filter_by(id=match_id).first()

    if not match:
        return failed_response(*match_not_found)

    group = Group.query.filter_by(id=match.group_id).first()

    return success_response(
        200,
        {
            "phase": group.phase.to_dict(),
            "group": group.to_dict_without_phase(),
            "match": match.to_dict_without_group(),
        },
    )


@matches.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches/groups/<string:group_name>")
@token_required
def matches_phases_get(current_user, group_name):
    group = Group.query.filter_by(code=group_name).first()
    phase = Phase.query.filter_by(id=group.phase_id).first()

    matches = Match.query.filter_by(group_id=group.id).order_by(Match.index)

    return success_response(
        200,
        {
            "phase": phase.to_dict(),
            "group": group.to_dict_without_phase(),
            "matches": [match.to_dict_without_group() for match in matches],
        },
    )


@matches.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches/teams/<string:team_id>")
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

    matches = (
        Match.query.join(Match.group)
        .join(Group.phase)
        .filter(or_(Match.team1_id == team.id, Match.team2_id == team.id))
        .order_by(desc(Phase.code), Group.code, Match.index)
    )

    group_query = (
        Group.query.join(Group.phase)
        .order_by(desc(Phase.code), Group.code)
        .filter(Group.id.in_(match.group_id for match in matches))
    )

    groups = [group.to_dict_with_phase_id() for group in group_query]

    phase_query = Phase.query.order_by(desc(Phase.code)).filter(
        Phase.id.in_(group.phase_id for group in group_query)
    )
    phases = [phase.to_dict() for phase in phase_query]

    return success_response(
        200,
        {
            "phases": phases,
            "groups": groups,
            "matches": [match.to_dict_with_group_id() for match in matches],
        },
    )
