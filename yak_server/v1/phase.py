from http import HTTPStatus

from flask import Blueprint

from yak_server.database.models import PhaseModel

from .utils.auth_utils import is_authentificated
from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import PhaseNotFound
from .utils.flask_utils import success_response

phase = Blueprint("phase", __name__)


@phase.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/phases")
@is_authentificated
def retrieve_all_phases(user):
    return success_response(
        HTTPStatus.OK,
        [phase.to_dict() for phase in PhaseModel.query.order_by(PhaseModel.index)],
    )


@phase.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/phases/<string:phase_id>")
@is_authentificated
def retrieve_by_phase_id(user, phase_id):
    phase = PhaseModel.query.filter_by(id=phase_id).first()

    if not phase:
        raise PhaseNotFound(phase_id)

    return success_response(HTTPStatus.OK, phase.to_dict())
