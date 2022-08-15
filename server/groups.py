from itertools import chain

from flask import Blueprint
from sqlalchemy import and_
from sqlalchemy import or_

from .models import Matches
from .models import Phase
from .models import Scores
from .models import Team
from .models import User
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
            sorted(
                (match.to_dict() for match in Matches.query.all()),
                key=lambda match: (match["phase"]["code"], match["index"]),
            ),
        )

    else:
        return failed_response(*unauthorized_access_to_admin_api)


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/results/<string:group_id>")
@token_required
def groups_results_by_group_id(current_user, group_id):
    # Retrieve admin scores for the specified group name
    admin = User.query.get(current_user.id)
    phase = Phase.query.filter_by(code=group_id).first()
    matches = Matches.query.filter_by(phase_id=phase.id)
    scores = Scores.query.filter(
        and_(
            Scores.user_id == admin.id,
            Scores.match_id.in_(map(lambda match: match.id, matches)),
        )
    )

    # Retrieve teams for the specified group name
    # and add specific results field (won, drawn, lost...)
    teams = ((match.team1, match.team2) for match in matches)
    teams = set(chain.from_iterable(teams))
    results = list(
        {
            "team": team.to_dict(),
            "results": {
                "played": 0,
                "won": 0,
                "drawn": 0,
                "lost": 0,
                "goal_for": 0,
                "goal_against": 0,
                "goal_diff": 0,
                "points": 0,
            },
        }
        for team in teams
    )

    for result in results:
        for score in scores:
            if score.score1 is not None and score.score2 is not None:
                if result["team"]["id"] == score.match.team1.id:
                    if score.score1 > score.score2:
                        won(result, score.score1, score.score2)
                    elif score.score1 == score.score2:
                        drawn(result, score.score1, score.score2)
                    else:
                        lost(result, score.score1, score.score2)
                elif result["team"]["id"] == score.match.team2.id:
                    if score.score2 > score.score1:
                        won(result, score.score2, score.score1)
                    elif score.score1 == score.score2:
                        drawn(result, score.score2, score.score1)
                    else:
                        lost(result, score.score2, score.score1)

    return success_response(
        200, sorted(results, key=lambda x: x["results"]["points"], reverse=True)
    )


def won(result, goal_for, goal_against):
    result["results"]["played"] += 1
    result["results"]["won"] += 1
    result["results"]["goal_for"] += goal_for
    result["results"]["goal_against"] += goal_against
    result["results"]["goal_diff"] += goal_for - goal_against
    result["results"]["points"] += 3


def drawn(result, goal_for, goal_against):
    result["results"]["played"] += 1
    result["results"]["drawn"] += 1
    result["results"]["goal_for"] += goal_for
    result["results"]["goal_against"] += goal_against
    result["results"]["points"] += 1


def lost(result, goal_for, goal_against):
    result["results"]["played"] += 1
    result["results"]["lost"] += 1
    result["results"]["goal_for"] += goal_for
    result["results"]["goal_against"] += goal_against
    result["results"]["goal_diff"] += goal_for - goal_against


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
