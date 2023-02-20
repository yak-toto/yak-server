from flask import Blueprint

from yak_server.database.models import TeamModel

from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import InvalidTeamId, TeamNotFound
from .utils.flask_utils import is_iso_3166_1_alpha_2_code, is_uuid4, success_response

teams = Blueprint("team", __name__)


@teams.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/teams")
def teams_get():
    return success_response(
        200,
        {"teams": [team.to_dict() for team in TeamModel.query.all()]},
    )


@teams.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/teams/<string:team_id>")
def teams_get_by_id(team_id):
    if is_uuid4(team_id):
        team = TeamModel.query.filter_by(id=team_id).first()
    elif is_iso_3166_1_alpha_2_code(team_id):
        team = TeamModel.query.filter_by(code=team_id).first()
    else:
        raise InvalidTeamId(team_id)

    if not team:
        raise TeamNotFound(team_id)

    return success_response(200, {"team": team.to_dict()})
