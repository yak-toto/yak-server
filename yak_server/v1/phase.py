from http import HTTPStatus

from flask import Blueprint

from yak_server.database.models import PhaseModel

from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import PhaseNotFound
from .utils.flask_utils import success_response

phase = Blueprint("phase", __name__)


@phase.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/phases")
@token_required
def retrieve_all_phases(user):
    return success_response(
        HTTPStatus.OK,
        [phase.to_dict() for phase in PhaseModel.query.order_by(PhaseModel.index)],
    )


@phase.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/phases/<string:phase_id>")
@token_required
def retrieve_by_phase_id(user, phase_id):
    phase = PhaseModel.query.filter_by(id=phase_id).first()

    if not phase:
        raise PhaseNotFound(phase_id)

    return success_response(HTTPStatus.OK, phase.to_dict())
