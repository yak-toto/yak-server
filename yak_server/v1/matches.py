from itertools import chain

from flask import Blueprint
from sqlalchemy import or_

from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    TeamModel,
)
from yak_server.database.query import matches_from_group_code, matches_from_phase_code

from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import InvalidTeamId, MatchNotFound, TeamNotFound
from .utils.flask_utils import is_iso_3166_1_alpha_2_code, is_uuid4, success_response

matches = Blueprint("matches", __name__)


@matches.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches")
@token_required
def matches_get_all(current_user):
    binary_bets = (
        current_user.binary_bets.join(BinaryBetModel.match)
        .join(MatchModel.group)
        .order_by(GroupModel.index, MatchModel.index)
    )

    score_bets = (
        current_user.score_bets.join(ScoreBetModel.match)
        .join(MatchModel.group)
        .order_by(GroupModel.index, MatchModel.index)
    )

    groups = GroupModel.query.order_by(GroupModel.index)

    phases = PhaseModel.query.order_by(PhaseModel.index)

    return success_response(
        200,
        {
            "phases": [phase.to_dict() for phase in phases],
            "groups": [group.to_dict_with_phase_id() for group in groups],
            "matches": [
                bet.match.to_dict_with_group_id() for bet in chain(score_bets, binary_bets)
            ],
        },
    )


@matches.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches/<string:match_id>")
@token_required
def matches_get_by_id(current_user, match_id):
    bet = current_user.binary_bets.filter_by(match_id=match_id).first()

    if not bet:
        bet = current_user.score_bets.filter_by(match_id=match_id).first()

    if not bet:
        raise MatchNotFound(match_id)

    return success_response(
        200,
        {
            "phase": bet.match.group.phase.to_dict(),
            "group": bet.match.group.to_dict_without_phase(),
            "match": bet.match.to_dict_without_group(),
        },
    )


@matches.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches/groups/<string:group_code>")
@token_required
def matches_by_group_code(current_user, group_code):
    group, matches = matches_from_group_code(current_user, group_code)

    return success_response(
        200,
        {
            "phase": group.phase.to_dict(),
            "group": group.to_dict_without_phase(),
            "matches": [match.to_dict_without_group() for match in matches],
        },
    )


@matches.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches/phases/<string:phase_code>")
@token_required
def matches_by_phase_code(current_user, phase_code):
    phase, groups, matches = matches_from_phase_code(current_user, phase_code)

    return success_response(
        200,
        {
            "phase": phase.to_dict(),
            "group": [group.to_dict_without_phase() for group in groups],
            "matches": [match.to_dict_with_group_id() for match in matches],
        },
    )


@matches.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches/teams/<string:team_id>")
@token_required
def matches_teams_get(current_user, team_id):
    if is_uuid4(team_id):
        team = TeamModel.query.get(team_id)
    elif is_iso_3166_1_alpha_2_code(team_id):
        team = TeamModel.query.filter_by(code=team_id).first()
    else:
        raise InvalidTeamId(team_id)

    if not team:
        raise TeamNotFound(team_id)

    score_bets = (
        current_user.score_bets.join(ScoreBetModel.match)
        .join(MatchModel.group)
        .filter(or_(MatchModel.team1_id == team.id, MatchModel.team2_id == team.id))
        .order_by(GroupModel.index, MatchModel.index)
    )

    binary_bets = (
        current_user.binary_bets.join(BinaryBetModel.match)
        .join(MatchModel.group)
        .filter(or_(MatchModel.team1_id == team.id, MatchModel.team2_id == team.id))
        .order_by(GroupModel.index, MatchModel.index)
    )

    groups = {bet.match.group for bet in chain(score_bets, binary_bets)}

    phases = {group.phase for group in groups}

    return success_response(
        200,
        {
            "phases": [phase.to_dict() for phase in phases],
            "groups": [group.to_dict_with_phase_id() for group in groups],
            "matches": [
                bet.match.to_dict_with_group_id() for bet in chain(score_bets, binary_bets)
            ],
        },
    )
