from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from yak_server.database.models import GroupModel, PhaseModel, UserModel
from yak_server.helpers.language import DEFAULT_LANGUAGE, Lang
from yak_server.v1.helpers.auth import get_current_user
from yak_server.v1.helpers.database import get_db
from yak_server.v1.helpers.errors import GroupNotFound, PhaseNotFound
from yak_server.v1.models.generic import GenericOut
from yak_server.v1.models.groups import (
    AllGroupsResponse,
    GroupOut,
    GroupResponse,
    GroupsByPhaseCodeResponse,
    GroupWithPhaseIdOut,
)
from yak_server.v1.models.phases import PhaseOut

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("/")
def retrieve_all_groups(
    lang: Lang = DEFAULT_LANGUAGE,
    _: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenericOut[AllGroupsResponse]:
    groups = db.query(GroupModel).order_by(GroupModel.index)
    phases = db.query(PhaseModel).order_by(PhaseModel.index)

    return GenericOut(
        result=AllGroupsResponse(
            phases=[PhaseOut.from_instance(phase, lang) for phase in phases],
            groups=[GroupWithPhaseIdOut.from_instance(group, lang) for group in groups],
        ),
    )


@router.get("/{group_code}")
def retrieve_group_by_id(
    group_code: str,
    lang: Lang = DEFAULT_LANGUAGE,
    _: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenericOut[GroupResponse]:
    group = db.query(GroupModel).filter_by(code=group_code).first()

    if not group:
        raise GroupNotFound(group_code)

    return GenericOut(
        result=GroupResponse(
            phase=PhaseOut.from_instance(group.phase, lang),
            group=GroupOut.from_instance(group, lang),
        ),
    )


@router.get("/phases/{phase_code}")
def retrieve_groups_by_phase_code(
    phase_code: str,
    lang: Lang = DEFAULT_LANGUAGE,
    _: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenericOut[GroupsByPhaseCodeResponse]:
    phase = db.query(PhaseModel).filter_by(code=phase_code).first()

    if not phase:
        raise PhaseNotFound(phase_code)

    groups = db.query(GroupModel).order_by(GroupModel.index).filter_by(phase_id=phase.id)

    return GenericOut(
        result=GroupsByPhaseCodeResponse(
            phase=PhaseOut.from_instance(phase, lang),
            groups=[GroupOut.from_instance(group, lang) for group in groups],
        ),
    )
