from typing import Annotated

import pendulum
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    UserModel,
)
from yak_server.database.query import (
    bets_from_group_code,
    bets_from_phase_code,
)
from yak_server.helpers.bet_locking import is_locked
from yak_server.helpers.database import get_db
from yak_server.helpers.group_position import get_group_rank_with_code
from yak_server.helpers.language import DEFAULT_LANGUAGE, Lang
from yak_server.helpers.settings import get_lock_datetime
from yak_server.v1.helpers.auth import get_current_user
from yak_server.v1.helpers.errors import GroupNotFound, PhaseNotFound
from yak_server.v1.models.bets import (
    AllBetsResponse,
    BetsByGroupCodeResponse,
    BetsByPhaseCodeResponse,
    GroupRankResponse,
)
from yak_server.v1.models.binary_bets import BinaryBetOut, BinaryBetWithGroupIdOut
from yak_server.v1.models.generic import ErrorOut, GenericOut, ValidationErrorOut
from yak_server.v1.models.group_rank import GroupPositionOut
from yak_server.v1.models.groups import GroupOut, GroupWithPhaseIdOut
from yak_server.v1.models.phases import PhaseOut
from yak_server.v1.models.score_bets import ScoreBetOut, ScoreBetWithGroupIdOut

router = APIRouter(prefix="/bets", tags=["bets"])


@router.get(
    "/",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorOut},
    },
)
def retrieve_all_bets(
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    lock_datetime: Annotated[pendulum.DateTime, Depends(get_lock_datetime)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[AllBetsResponse]:
    binary_bets = (
        db.query(BinaryBetModel)
        .join(BinaryBetModel.match)
        .filter(MatchModel.user_id == user.id)
        .join(MatchModel.group)
        .order_by(GroupModel.index, MatchModel.index)
    )

    score_bets = (
        db.query(ScoreBetModel)
        .join(ScoreBetModel.match)
        .filter(MatchModel.user_id == user.id)
        .join(MatchModel.group)
        .order_by(GroupModel.index, MatchModel.index)
    )

    groups = db.query(GroupModel).order_by(GroupModel.index)
    phases = db.query(PhaseModel).order_by(PhaseModel.index)

    return GenericOut(
        result=AllBetsResponse(
            phases=[PhaseOut.from_instance(phase, lang=lang) for phase in phases],
            groups=[GroupWithPhaseIdOut.from_instance(group, lang=lang) for group in groups],
            score_bets=[
                ScoreBetWithGroupIdOut.from_instance(
                    score_bet,
                    locked=is_locked(user.name, lock_datetime),
                    lang=lang,
                )
                for score_bet in score_bets
            ],
            binary_bets=[
                BinaryBetWithGroupIdOut.from_instance(
                    binary_bet,
                    locked=is_locked(user.name, lock_datetime),
                    lang=lang,
                )
                for binary_bet in binary_bets
            ],
        ),
    )


@router.get(
    "/phases/{phase_code}",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorOut},
    },
)
def retrieve_bets_by_phase_code(
    phase_code: str,
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    lock_datetime: Annotated[pendulum.DateTime, Depends(get_lock_datetime)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[BetsByPhaseCodeResponse]:
    phase, groups, score_bets, binary_bets = bets_from_phase_code(db, user, phase_code)

    if not phase:
        raise PhaseNotFound(phase_code)

    return GenericOut(
        result=BetsByPhaseCodeResponse(
            phase=PhaseOut.from_instance(phase, lang=lang),
            groups=[GroupOut.from_instance(group, lang=lang) for group in groups],
            score_bets=[
                ScoreBetWithGroupIdOut.from_instance(
                    score_bet,
                    locked=is_locked(user.name, lock_datetime),
                    lang=lang,
                )
                for score_bet in score_bets
            ],
            binary_bets=[
                BinaryBetWithGroupIdOut.from_instance(
                    binary_bet,
                    locked=is_locked(user.name, lock_datetime),
                    lang=lang,
                )
                for binary_bet in binary_bets
            ],
        ),
    )


@router.get(
    "/groups/{group_code}",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorOut},
    },
)
def retrieve_bets_by_group_code(
    group_code: str,
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    lock_datetime: Annotated[pendulum.DateTime, Depends(get_lock_datetime)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[BetsByGroupCodeResponse]:
    group, score_bets, binary_bets = bets_from_group_code(db, user, group_code)

    if not group:
        raise GroupNotFound(group_code)

    return GenericOut(
        result=BetsByGroupCodeResponse(
            phase=PhaseOut.from_instance(group.phase, lang=lang),
            group=GroupOut.from_instance(group, lang=lang),
            score_bets=[
                ScoreBetOut.from_instance(
                    score_bet,
                    locked=is_locked(user.name, lock_datetime),
                    lang=lang,
                )
                for score_bet in score_bets
            ],
            binary_bets=[
                BinaryBetOut.from_instance(
                    binary_bet,
                    locked=is_locked(user.name, lock_datetime),
                    lang=lang,
                )
                for binary_bet in binary_bets
            ],
        ),
    )


@router.get(
    "/groups/rank/{group_code}",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorOut},
    },
)
def retrieve_group_rank_by_code(
    group_code: str,
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[GroupRankResponse]:
    group = db.query(GroupModel).filter_by(code=group_code).first()

    if not group:
        raise GroupNotFound(group_code)

    group_rank = get_group_rank_with_code(db, user, group.id)

    return GenericOut(
        result=GroupRankResponse(
            phase=PhaseOut.from_instance(group.phase, lang=lang),
            group=GroupOut.from_instance(group, lang=lang),
            group_rank=[
                GroupPositionOut.from_instance(group_position, lang=lang)
                for group_position in group_rank
            ],
        ),
    )
