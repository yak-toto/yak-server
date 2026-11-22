from fastapi import APIRouter, Depends, status
from pydantic import UUID4

from yak_server.database.models import PhaseModel
from yak_server.helpers.database import SessionDep
from yak_server.helpers.language import DEFAULT_LANGUAGE, LangQuery
from yak_server.v1.helpers.auth import require_user
from yak_server.v1.helpers.errors import PhaseNotFound
from yak_server.v1.helpers.responses import error_responses
from yak_server.v1.models.generic import GenericOut
from yak_server.v1.models.phases import PhaseOut

router = APIRouter(
    prefix="/phases",
    tags=["phases"],
    dependencies=[Depends(require_user)],
    responses=error_responses(status.HTTP_401_UNAUTHORIZED),
)


@router.get("")
def retrieve_all_phases(
    db: SessionDep,
    lang: LangQuery = DEFAULT_LANGUAGE,
) -> GenericOut[list[PhaseOut]]:
    return GenericOut(
        result=[
            PhaseOut.from_instance(phase, lang=lang)
            for phase in db.query(PhaseModel).order_by(PhaseModel.index)
        ],
    )


@router.get(
    "/{phase_id}",
    responses=error_responses(status.HTTP_404_NOT_FOUND),
)
def retrieve_phase(
    phase_id: UUID4,
    db: SessionDep,
    lang: LangQuery = DEFAULT_LANGUAGE,
) -> GenericOut[PhaseOut]:
    phase = db.query(PhaseModel).filter_by(id=phase_id).first()

    if not phase:
        raise PhaseNotFound(phase_id)

    return GenericOut(
        result=PhaseOut.from_instance(phase, lang=lang),
    )
