from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session, selectinload

from yak_server.database.models import GroupModel, PhaseModel, UserModel
from yak_server.helpers.database import get_db
from yak_server.helpers.language import DEFAULT_LANGUAGE, Lang
from yak_server.v1.helpers.auth import require_user
from yak_server.v1.helpers.errors import GroupNotFound, PhaseNotFound
from yak_server.v1.models.generic import ErrorOut, GenericOut, ValidationErrorOut
from yak_server.v1.models.groups import (
    AllGroupsResponse,
    GroupOut,
    GroupResponse,
    GroupsByPhaseCodeResponse,
    GroupWithPhaseIdOut,
)
from yak_server.v1.models.phases import PhaseOut

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get(
    "/",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut},
    },
)
def retrieve_all_groups(
    _: Annotated[UserModel, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
    lang: Lang = DEFAULT_LANGUAGE,
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
    "/{group_code}",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut},
    },
)
def retrieve_group_by_id(
    group_code: str,
    _: Annotated[UserModel, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[GroupResponse]:
    group = (
        db
        .query(GroupModel)
        .options(selectinload(GroupModel.phase))
        .filter_by(code=group_code)
        .first()
    )

    if group is None:
        raise GroupNotFound(group_code)

    return GenericOut(
        result=GroupResponse(
            phase=PhaseOut.from_instance(group.phase, lang=lang),
            group=GroupOut.from_instance(group, lang=lang),
        ),
    )


@router.get(
    "/phases/{phase_code}",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut},
    },
)
def retrieve_groups_by_phase_code(
    phase_code: str,
    _: Annotated[UserModel, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
    lang: Lang = DEFAULT_LANGUAGE,
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
