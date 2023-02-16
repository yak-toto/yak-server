from flask import Blueprint, request

from yak_server import db
from yak_server.database.models import TeamModel

from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import InvalidTeamId, TeamNotFound
from .utils.flask_utils import is_iso_3166_1_alpha_2_code, is_uuid4, success_response

teams = Blueprint("team", __name__)


@teams.post(f"/{GLOBAL_ENDPOINT}/{VERSION}/teams")
def teams_post():
    body = request.get_json()

    if isinstance(body, list):
        teams = [TeamModel(**team) for team in body]

        db.session.add_all(teams)
        db.session.commit()

        return success_response(201, {"teams": [team.to_dict() for team in teams]})
    else:
        team = TeamModel(**body)

        db.session.add(team)
        db.session.commit()

        return success_response(201, {"team": team.to_dict()})


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
