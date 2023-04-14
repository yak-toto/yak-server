from http import HTTPStatus
from typing import TYPE_CHECKING, Tuple

from flask import Blueprint

from yak_server.database.models import PhaseModel, get_db

from .utils.auth_utils import is_authentificated
from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import PhaseNotFound
from .utils.flask_utils import success_response

if TYPE_CHECKING:
    from flask import Response


phase = Blueprint("phase", __name__)


@phase.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/phases")
@is_authentificated
def retrieve_all_phases(_) -> Tuple["Response", int]:
    db = get_db()

    return success_response(
        HTTPStatus.OK,
        [phase.to_dict() for phase in db.query(PhaseModel).order_by(PhaseModel.index)],
    )


@phase.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/phases/<string:phase_id>")
@is_authentificated
def retrieve_by_phase_id(_, phase_id) -> Tuple["Response", int]:
    db = get_db()

    phase = db.query(PhaseModel).filter_by(id=phase_id).first()

    if not phase:
        raise PhaseNotFound(phase_id)

    return success_response(HTTPStatus.OK, phase.to_dict())
