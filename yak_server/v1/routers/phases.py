from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import UUID4
from sqlalchemy.orm import Session

from yak_server.database.models import PhaseModel, UserModel
from yak_server.helpers.database import get_db
from yak_server.helpers.language import DEFAULT_LANGUAGE, Lang
from yak_server.v1.helpers.auth import require_user
from yak_server.v1.helpers.errors import PhaseNotFound
from yak_server.v1.models.generic import ErrorOut, GenericOut, ValidationErrorOut
from yak_server.v1.models.phases import PhaseOut

router = APIRouter(prefix="/phases", tags=["phases"])


@router.get(
    "/",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut},
    },
)
def retrieve_all_phases(
    _: Annotated[UserModel, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[list[PhaseOut]]:
    return GenericOut(
        result=[
            PhaseOut.from_instance(phase, lang=lang)
            for phase in db.query(PhaseModel).order_by(PhaseModel.index)
        ],
    )


@router.get(
    "/{phase_id}",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut},
    },
)
def retrieve_phase(
    phase_id: UUID4,
    _: Annotated[UserModel, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[PhaseOut]:
    phase = db.query(PhaseModel).filter_by(id=phase_id).first()

    if not phase:
        raise PhaseNotFound(phase_id)

    return GenericOut(
        result=PhaseOut.from_instance(phase, lang=lang),
    )
