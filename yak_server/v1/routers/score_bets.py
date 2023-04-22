import logging

from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yak_server.config_file import Settings, get_settings
from yak_server.database.models import (
    GroupPositionModel,
    MatchModel,
    ScoreBetModel,
    UserModel,
)
from yak_server.helpers.bet_locking import is_locked
from yak_server.helpers.logging import modify_score_bet_successfully
from yak_server.v1.helpers.auth import get_current_user
from yak_server.v1.helpers.database import get_db
from yak_server.v1.helpers.errors import (
    BetNotFound,
    GroupNotFound,
    LockedScoreBet,
    TeamNotFound,
)
from yak_server.v1.models.generic import GenericOut
from yak_server.v1.models.groups import GroupOut
from yak_server.v1.models.phases import PhaseOut
from yak_server.v1.models.score_bets import (
    ModifyScoreBetIn,
    ScoreBetIn,
    ScoreBetOut,
    ScoreBetResponse,
)
from yak_server.v1.models.teams import FlagOut, TeamWithScoreOut

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/score_bets",
    tags=["score_bets"],
)


def send_response(
    score_bet: ScoreBetModel,
    locked: bool,  # noqa: FBT001
) -> GenericOut[ScoreBetResponse]:
    return GenericOut(
        result=ScoreBetResponse(
            phase=PhaseOut.from_orm(score_bet.match.group.phase),
            group=GroupOut.from_orm(score_bet.match.group),
            score_bet=ScoreBetOut(
                id=score_bet.id,
                locked=locked,
                team1=TeamWithScoreOut(
                    id=score_bet.match.team1.id,
                    code=score_bet.match.team1.code,
                    description=score_bet.match.team1.description,
                    flag=FlagOut(url=score_bet.match.team1.flag_url),
                    score=score_bet.score1,
                ),
                team2=TeamWithScoreOut(
                    id=score_bet.match.team2.id,
                    code=score_bet.match.team2.code,
                    description=score_bet.match.team2.description,
                    flag=FlagOut(url=score_bet.match.team2.flag_url),
                    score=score_bet.score2,
                ),
            ),
        ),
    )


@router.post("/")
def create_score_bet(
    score_bet_in: ScoreBetIn,
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> GenericOut[ScoreBetResponse]:
    if is_locked(user.name, settings.lock_datetime):
        raise LockedScoreBet

    match = MatchModel(
        team1_id=score_bet_in.team1.id,
        team2_id=score_bet_in.team2.id,
        index=score_bet_in.index,
        group_id=score_bet_in.group.id,
    )

    db.add(match)
    try:
        db.flush()
    except IntegrityError as integrity_error:
        if "FOREIGN KEY (`team1_id`)" in str(integrity_error):
            raise TeamNotFound(team_id=score_bet_in.team1.id) from integrity_error

        if "FOREIGN KEY (`team2_id`)" in str(integrity_error):
            raise TeamNotFound(team_id=score_bet_in.team2.id) from integrity_error

        raise GroupNotFound(group_id=score_bet_in.group.id) from integrity_error

    score_bet = ScoreBetModel(
        match_id=match.id,
        user_id=user.id,
        score1=score_bet_in.team1.score,
        score2=score_bet_in.team2.score,
    )

    db.execute(
        update(GroupPositionModel)
        .values(need_recomputation=True)
        .where(
            GroupPositionModel.team_id == score_bet_in.team1.id,
            GroupPositionModel.user_id == user.id,
        ),
    )
    db.execute(
        update(GroupPositionModel)
        .values(need_recomputation=True)
        .where(
            GroupPositionModel.team_id == score_bet_in.team2.id,
            GroupPositionModel.user_id == user.id,
        ),
    )

    db.add(score_bet)
    db.commit()
    db.refresh(score_bet)

    return send_response(score_bet, is_locked(user.name, settings.lock_datetime))


@router.get("/{bet_id}")
def retrieve_score_bet_by_id(
    bet_id: UUID4,
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> GenericOut[ScoreBetResponse]:
    score_bet = db.query(ScoreBetModel).filter_by(user_id=user.id, id=str(bet_id)).first()

    if not score_bet:
        raise BetNotFound(bet_id)

    return send_response(score_bet, is_locked(user.name, settings.lock_datetime))


@router.patch("/{bet_id}")
def modify_score_bet(
    bet_id: UUID4,
    modify_score_bet_in: ModifyScoreBetIn,
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> GenericOut[ScoreBetResponse]:
    if is_locked(user.name, settings.lock_datetime):
        raise LockedScoreBet

    score_bet = (
        db.query(ScoreBetModel).filter_by(user_id=user.id, id=str(bet_id)).with_for_update().first()
    )

    if not score_bet:
        raise BetNotFound(bet_id)

    if (
        score_bet.score1 == modify_score_bet_in.team1.score
        and score_bet.score2 == modify_score_bet_in.team2.score
    ):
        return send_response(score_bet, is_locked(user.name, settings.lock_datetime))

    logger.info(
        modify_score_bet_successfully(
            user.name,
            score_bet,
            modify_score_bet_in.team1.score,
            modify_score_bet_in.team2.score,
        ),
    )

    db.execute(
        update(GroupPositionModel)
        .values(need_recomputation=True)
        .where(
            GroupPositionModel.team_id == score_bet.match.team1_id,
            GroupPositionModel.user_id == user.id,
        ),
    )
    db.execute(
        update(GroupPositionModel)
        .values(need_recomputation=True)
        .where(
            GroupPositionModel.team_id == score_bet.match.team2_id,
            GroupPositionModel.user_id == user.id,
        ),
    )

    score_bet.score1 = modify_score_bet_in.team1.score
    score_bet.score2 = modify_score_bet_in.team2.score
    db.commit()

    return send_response(score_bet, is_locked(user.name, settings.lock_datetime))


@router.delete("/{bet_id}")
def delete_score_bet_by_id(
    bet_id: UUID4,
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> GenericOut[ScoreBetResponse]:
    if is_locked(user.name, settings.lock_datetime):
        raise LockedScoreBet

    score_bet = db.query(ScoreBetModel).filter_by(user_id=user.id, id=str(bet_id)).first()

    if not score_bet:
        raise BetNotFound(bet_id)

    response = send_response(score_bet, is_locked(user.name, settings.lock_datetime))

    db.execute(
        update(GroupPositionModel)
        .values(need_recomputation=True)
        .where(
            GroupPositionModel.team_id == score_bet.match.team1_id,
            GroupPositionModel.user_id == user.id,
        ),
    )
    db.execute(
        update(GroupPositionModel)
        .values(need_recomputation=True)
        .where(
            GroupPositionModel.team_id == score_bet.match.team2_id,
            GroupPositionModel.user_id == user.id,
        ),
    )

    db.delete(score_bet)
    db.commit()

    return response
