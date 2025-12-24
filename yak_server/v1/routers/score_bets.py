import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import UUID4
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from yak_server.database.models import GroupModel, MatchModel, ScoreBetModel, UserModel
from yak_server.helpers.bet_locking import is_locked
from yak_server.helpers.database import get_db
from yak_server.helpers.group_position import set_recomputation_flag
from yak_server.helpers.language import DEFAULT_LANGUAGE, Lang, get_language_description
from yak_server.helpers.logging_helpers import modify_score_bet_successfully
from yak_server.helpers.settings import get_lock_datetime
from yak_server.v1.helpers.auth import require_user
from yak_server.v1.helpers.errors import BetNotFound, LockedScoreBet, TeamNotFound
from yak_server.v1.models.generic import ErrorOut, GenericOut, ValidationErrorOut
from yak_server.v1.models.groups import GroupOut
from yak_server.v1.models.phases import PhaseOut
from yak_server.v1.models.score_bets import ModifyScoreBetIn, ScoreBetOut, ScoreBetResponse
from yak_server.v1.models.teams import FlagOut, TeamWithScoreOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/score_bets", tags=["score_bets"])


def send_response(
    score_bet: ScoreBetModel,
    *,
    locked: bool,
    lang: Lang,
) -> GenericOut[ScoreBetResponse]:
    return GenericOut(
        result=ScoreBetResponse(
            phase=PhaseOut.from_instance(score_bet.match.group.phase, lang=lang),
            group=GroupOut.from_instance(score_bet.match.group, lang=lang),
            score_bet=ScoreBetOut(
                id=score_bet.id,
                locked=locked,
                team1=(
                    TeamWithScoreOut(
                        id=score_bet.match.team1.id,
                        code=score_bet.match.team1.code,
                        description=get_language_description(score_bet.match.team1, lang),
                        flag=FlagOut(url=score_bet.match.team1.flag_url),
                        score=score_bet.score1,
                    )
                    if score_bet.match.team1 is not None
                    else None
                ),
                team2=(
                    TeamWithScoreOut(
                        id=score_bet.match.team2.id,
                        code=score_bet.match.team2.code,
                        description=get_language_description(score_bet.match.team2, lang),
                        flag=FlagOut(url=score_bet.match.team2.flag_url),
                        score=score_bet.score2,
                    )
                    if score_bet.match.team2 is not None
                    else None
                ),
            ),
        ),
    )


@router.get(
    "/{bet_id}",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut},
    },
)
def retrieve_score_bet_by_id(
    bet_id: UUID4,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[UserModel, Depends(require_user)],
    lock_datetime: Annotated[datetime, Depends(get_lock_datetime)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[ScoreBetResponse]:
    score_bet = (
        db
        .query(ScoreBetModel)
        .options(
            selectinload(ScoreBetModel.match)
            .selectinload(MatchModel.group)
            .selectinload(GroupModel.phase),
            selectinload(ScoreBetModel.match).selectinload(MatchModel.team1),
            selectinload(ScoreBetModel.match).selectinload(MatchModel.team2),
        )
        .join(ScoreBetModel.match)
        .where(MatchModel.user_id == user.id, ScoreBetModel.id == bet_id)
        .first()
    )

    if not score_bet:
        raise BetNotFound(bet_id)

    return send_response(score_bet, locked=is_locked(user, lock_datetime), lang=lang)


@router.patch(
    "/{bet_id}",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut},
    },
)
def modify_score_bet(
    bet_id: UUID4,
    modify_score_bet_in: ModifyScoreBetIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[UserModel, Depends(require_user)],
    lock_datetime: Annotated[datetime, Depends(get_lock_datetime)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[ScoreBetResponse]:
    if is_locked(user, lock_datetime):
        raise LockedScoreBet

    score_bet = (
        db
        .query(ScoreBetModel)
        .options(
            selectinload(ScoreBetModel.match)
            .selectinload(MatchModel.group)
            .selectinload(GroupModel.phase),
            selectinload(ScoreBetModel.match).selectinload(MatchModel.team1),
            selectinload(ScoreBetModel.match).selectinload(MatchModel.team2),
        )
        .join(ScoreBetModel.match)
        .where(MatchModel.user_id == user.id, ScoreBetModel.id == bet_id)
        .with_for_update()
        .first()
    )

    if not score_bet:
        raise BetNotFound(bet_id)

    logger.info(
        modify_score_bet_successfully(
            user.name,
            score_bet,
            modify_score_bet_in.team1.score if modify_score_bet_in.team1 else None,
            modify_score_bet_in.team2.score if modify_score_bet_in.team2 else None,
        ),
    )

    if modify_score_bet_in.team1 is not None:
        if "id" in modify_score_bet_in.team1.model_fields_set:
            score_bet.match.team1_id = modify_score_bet_in.team1.id

            try:
                db.flush()
            except IntegrityError as integrity_error:
                db.rollback()
                # team1.id is not None due to: "id" in modify_score_bet_in.team1.model_fields_set
                # being true
                raise TeamNotFound(modify_score_bet_in.team1.id) from integrity_error  # type: ignore[arg-type]

        if "score" in modify_score_bet_in.team1.model_fields_set:
            score_bet.score1 = modify_score_bet_in.team1.score

    if modify_score_bet_in.team2 is not None:
        if "id" in modify_score_bet_in.team2.model_fields_set:
            score_bet.match.team2_id = modify_score_bet_in.team2.id

            try:
                db.flush()
            except IntegrityError as integrity_error:
                db.rollback()
                # team2.id is not None due to: "id" in modify_score_bet_in.team2.model_fields_set
                # being true
                raise TeamNotFound(modify_score_bet_in.team2.id) from integrity_error  # type: ignore[arg-type]

        if "score" in modify_score_bet_in.team2.model_fields_set:
            score_bet.score2 = modify_score_bet_in.team2.score

    set_recomputation_flag(db, score_bet.match.team1_id, user.id)
    set_recomputation_flag(db, score_bet.match.team2_id, user.id)

    db.commit()
    db.refresh(score_bet)

    return send_response(score_bet, locked=is_locked(user, lock_datetime), lang=lang)
