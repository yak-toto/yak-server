from flask import Blueprint

from .models import Team
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.flask_utils import success_response

teams = Blueprint("team", __name__)


@teams.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/teams")
def teams_get():
    return success_response(200, [team.to_dict() for team in Team.query.all()])
