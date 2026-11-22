from fastapi import APIRouter, Depends, status
from pydantic import UUID4
from sqlalchemy.orm import selectinload

from yak_server.database.models import GroupModel, PhaseModel
from yak_server.helpers.database import SessionDep
from yak_server.helpers.language import DEFAULT_LANGUAGE, LangQuery
from yak_server.v1.helpers.auth import require_user
from yak_server.v1.helpers.errors import GroupNotFound, PhaseNotFound
from yak_server.v1.helpers.responses import error_responses
from yak_server.v1.models.generic import GenericOut
from yak_server.v1.models.groups import (
    AllGroupsResponse,
    GroupOut,
    GroupResponse,
    GroupsByPhaseCodeResponse,
    GroupWithPhaseIdOut,
)
from yak_server.v1.models.phases import PhaseOut

router = APIRouter(
    prefix="/groups",
    tags=["groups"],
    dependencies=[Depends(require_user)],
    responses=error_responses(status.HTTP_401_UNAUTHORIZED),
)


@router.get("")
def retrieve_all_groups(
    db: SessionDep,
    lang: LangQuery = DEFAULT_LANGUAGE,
) -> GenericOut[AllGroupsResponse]:
    groups = db.query(GroupModel).order_by(GroupModel.index)
    phases = db.query(PhaseModel).order_by(PhaseModel.index)

    return GenericOut(
        result=AllGroupsResponse(
            phases=[PhaseOut.from_instance(phase, lang=lang) for phase in phases],
            groups=[GroupWithPhaseIdOut.from_instance(group, lang=lang) for group in groups],
        ),
    )


@router.get(
    "/{group_id}",
    responses=error_responses(status.HTTP_404_NOT_FOUND),
)
def retrieve_group_by_id(
    group_id: UUID4,
    db: SessionDep,
    lang: LangQuery = DEFAULT_LANGUAGE,
) -> GenericOut[GroupResponse]:
    group = (
        db.query(GroupModel).options(selectinload(GroupModel.phase)).filter_by(id=group_id).first()
    )

    if group is None:
        raise GroupNotFound(group_id)

    return GenericOut(
        result=GroupResponse(
            phase=PhaseOut.from_instance(group.phase, lang=lang),
            group=GroupOut.from_instance(group, lang=lang),
        ),
    )


@router.get(
    "/phases/{phase_code}",
    responses=error_responses(status.HTTP_404_NOT_FOUND),
)
def retrieve_groups_by_phase_code(
    phase_code: str,
    db: SessionDep,
    lang: LangQuery = DEFAULT_LANGUAGE,
) -> GenericOut[GroupsByPhaseCodeResponse]:
    phase = db.query(PhaseModel).filter_by(code=phase_code).first()

    if not phase:
        raise PhaseNotFound(phase_code)

    groups = db.query(GroupModel).order_by(GroupModel.index).filter_by(phase_id=phase.id)

    return GenericOut(
        result=GroupsByPhaseCodeResponse(
            phase=PhaseOut.from_instance(phase, lang=lang),
            groups=[GroupOut.from_instance(group, lang=lang) for group in groups],
        ),
    )
