from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from yak_server.config_file import Settings, get_settings
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
from yak_server.helpers.group_position import get_group_rank_with_code
from yak_server.v1.helpers.auth import get_current_user
from yak_server.v1.helpers.database import get_db
from yak_server.v1.helpers.errors import GroupNotFound, PhaseNotFound
from yak_server.v1.models.bets import (
    AllBetsResponse,
    BetsByGroupCodeResponse,
    BetsByPhaseCodeResponse,
    GroupRankResponse,
)
from yak_server.v1.models.binary_bets import BinaryBetOut, BinaryBetWithGroupIdOut
from yak_server.v1.models.generic import GenericOut
from yak_server.v1.models.group_rank import GroupPositionOut
from yak_server.v1.models.groups import GroupOut, GroupWithPhaseIdOut
from yak_server.v1.models.phases import PhaseOut
from yak_server.v1.models.score_bets import ScoreBetOut, ScoreBetWithGroupIdOut

router = APIRouter(
    prefix="/bets",
    tags=["bets"],
)


@router.get("/")
def retrieve_all_bets(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> GenericOut[AllBetsResponse]:
    binary_bets = (
        user.binary_bets.join(BinaryBetModel.match)
        .join(MatchModel.group)
        .order_by(GroupModel.index, MatchModel.index)
    )

    score_bets = (
        user.score_bets.join(ScoreBetModel.match)
        .join(MatchModel.group)
        .order_by(GroupModel.index, MatchModel.index)
    )

    groups = db.query(GroupModel).order_by(GroupModel.index)
    phases = db.query(PhaseModel).order_by(PhaseModel.index)

    return GenericOut(
        result=AllBetsResponse(
            phases=[PhaseOut.from_instance(phase) for phase in phases],
            groups=[GroupWithPhaseIdOut.from_instance(group) for group in groups],
            score_bets=[
                ScoreBetWithGroupIdOut.from_instance(
                    score_bet,
                    is_locked(user.name, settings.lock_datetime),
                )
                for score_bet in score_bets
            ],
            binary_bets=[
                BinaryBetWithGroupIdOut.from_instance(
                    binary_bet,
                    is_locked(user.name, settings.lock_datetime),
                )
                for binary_bet in binary_bets
            ],
        ),
    )


@router.get("/phases/{phase_code}")
def retrieve_bets_by_phase_code(
    phase_code: str,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> GenericOut[BetsByPhaseCodeResponse]:
    phase, groups, score_bets, binary_bets = bets_from_phase_code(
        db,
        user,
        phase_code,
    )

    if not phase:
        raise PhaseNotFound(phase_code)

    return GenericOut(
        result=BetsByPhaseCodeResponse(
            phase=PhaseOut.from_instance(phase),
            groups=[GroupOut.from_instance(group) for group in groups],
            score_bets=[
                ScoreBetWithGroupIdOut.from_instance(
                    score_bet,
                    is_locked(user.name, settings.lock_datetime),
                )
                for score_bet in score_bets
            ],
            binary_bets=[
                BinaryBetWithGroupIdOut.from_instance(
                    binary_bet,
                    is_locked(user.name, settings.lock_datetime),
                )
                for binary_bet in binary_bets
            ],
        ),
    )


@router.get("/groups/{group_code}")
def retrieve_bets_by_group_code(
    group_code: str,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> GenericOut[BetsByGroupCodeResponse]:
    group, score_bets, binary_bets = bets_from_group_code(db, user, group_code)

    if not group:
        raise GroupNotFound(group_code)

    return GenericOut(
        result=BetsByGroupCodeResponse(
            phase=PhaseOut.from_instance(group.phase),
            group=GroupOut.from_instance(group),
            score_bets=[
                ScoreBetOut.from_instance(score_bet, is_locked(user.name, settings.lock_datetime))
                for score_bet in score_bets
            ],
            binary_bets=[
                BinaryBetOut.from_instance(binary_bet, is_locked(user.name, settings.lock_datetime))
                for binary_bet in binary_bets
            ],
        ),
    )


@router.get("/groups/rank/{group_code}")
def retrieve_group_rank_by_code(
    group_code: str,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenericOut[GroupRankResponse]:
    group = db.query(GroupModel).filter_by(code=group_code).first()

    if not group:
        raise GroupNotFound(group_code)

    group_rank = get_group_rank_with_code(db, user, group.id)

    return GenericOut(
        result=GroupRankResponse(
            phase=PhaseOut.from_instance(group.phase),
            group=GroupOut.from_instance(group),
            group_rank=[
                GroupPositionOut.from_instance(group_position) for group_position in group_rank
            ],
        ),
    )
