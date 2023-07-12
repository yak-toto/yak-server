from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from yak_server.database.models import PhaseModel, UserModel
from yak_server.helpers.language import DEFAULT_LANGUAGE, Lang
from yak_server.v1.helpers.auth import get_current_user
from yak_server.v1.helpers.database import get_db
from yak_server.v1.helpers.errors import PhaseNotFound
from yak_server.v1.models.generic import GenericOut
from yak_server.v1.models.phases import PhaseOut

if TYPE_CHECKING:
    from pydantic import UUID4
    from sqlalchemy.orm import Session

router = APIRouter(prefix="/phases", tags=["phases"])


@router.get("/")
def retrieve_all_phases(
    lang: Lang = DEFAULT_LANGUAGE,
    _: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenericOut[list[PhaseOut]]:
    return GenericOut(
        result=[
            PhaseOut.from_instance(phase, lang)
            for phase in db.query(PhaseModel).order_by(PhaseModel.index)
        ],
    )


@router.get("/{phase_id}")
def retrieve_phase(
    phase_id: UUID4,
    lang: Lang = DEFAULT_LANGUAGE,
    _: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenericOut[PhaseOut]:
    phase = db.query(PhaseModel).filter_by(id=str(phase_id)).first()

    if not phase:
        raise PhaseNotFound(phase_id)

    return GenericOut(
        result=PhaseOut.from_instance(phase, lang),
    )
