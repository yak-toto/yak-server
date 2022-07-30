from flask import Blueprint

from .models import Matches
from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.errors import unauthorized_access_to_admin_api
from .utils.flask_utils import failed_response
from .utils.flask_utils import success_response

groups = Blueprint("group", __name__)


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/names")
@token_required
def groups_names(current_user):
    return success_response(
        200, sorted(list({match.group_name for match in Matches.query.all()}))
    )


@groups.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches")
@token_required
def matches(current_user):
    if current_user.name in ("admin"):
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
