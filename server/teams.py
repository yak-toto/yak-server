from flask import Blueprint

from .models import Team
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.errors import invalid_team_id
from .utils.errors import team_not_found
from .utils.flask_utils import failed_response
from .utils.flask_utils import is_iso_3166_1_alpha_2_code
from .utils.flask_utils import is_uuid4
from .utils.flask_utils import success_response

teams = Blueprint("team", __name__)


@teams.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/teams")
def teams_get():
    return success_response(200, [team.to_dict() for team in Team.query.all()])


@teams.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/teams/<string:team_id>")
def teams_get_by_id(team_id):
    if is_uuid4(team_id):
        team = Team.query.get(team_id)
    elif is_iso_3166_1_alpha_2_code(team_id):
        team = Team.query.filter_by(code=team_id).first()
    else:
        return failed_response(*invalid_team_id)

    if not team:
        return failed_response(*team_not_found)

    return success_response(200, team.to_dict())
