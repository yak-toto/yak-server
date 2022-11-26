from flask import Blueprint
from flask import request

from . import db
from .models import Team
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.errors import InvalidTeamId
from .utils.errors import TeamNotFound
from .utils.flask_utils import is_iso_3166_1_alpha_2_code
from .utils.flask_utils import is_uuid4
from .utils.flask_utils import success_response

teams = Blueprint("team", __name__)


@teams.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/teams", methods=["POST"])
def teams_post():
    body = request.get_json()

    if isinstance(body, list):
        teams = [Team(**team) for team in body]

        db.session.add_all(teams)
        db.session.commit()

        return success_response(201, {"teams": [team.to_dict() for team in teams]})
    else:
        team = Team(**body)

        db.session.add(team)
        db.session.commit()

        return success_response(201, {"team": team.to_dict()})


@teams.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/teams")
def teams_get():
    return success_response(
        200, {"teams": [team.to_dict() for team in Team.query.all()]}
    )


@teams.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/teams/<string:team_id>")
def teams_get_by_id(team_id):
    if is_uuid4(team_id):
        team = Team.query.get(team_id)
    elif is_iso_3166_1_alpha_2_code(team_id):
        team = Team.query.filter_by(code=team_id).first()
    else:
        raise InvalidTeamId(team_id)

    if not team:
        raise TeamNotFound(team_id)

    return success_response(200, {"team": team.to_dict()})
