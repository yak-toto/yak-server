import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yak_server.database.models import (
    MatchModel,
    ScoreBetModel,
    UserModel,
)
from yak_server.helpers.bet_locking import is_locked
from yak_server.helpers.database import get_db
from yak_server.helpers.group_position import set_recomputation_flag
from yak_server.helpers.language import DEFAULT_LANGUAGE, Lang, get_language_description
from yak_server.helpers.logging_helpers import modify_score_bet_successfully
from yak_server.helpers.settings import Settings, get_settings
from yak_server.v1.helpers.auth import get_current_user
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
                    if score_bet.match.team1_id is not None
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
                    if score_bet.match.team2_id is not None
                    else None
                ),
            ),
        ),
    )


@router.post("/")
def create_score_bet(
    score_bet_in: ScoreBetIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[UserModel, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[ScoreBetResponse]:
    if is_locked(user.name, settings.lock_datetime):
        raise LockedScoreBet

    match = MatchModel(
        team1_id=score_bet_in.team1.id,
        team2_id=score_bet_in.team2.id,
        index=score_bet_in.index,
        group_id=score_bet_in.group.id,
        user_id=user.id,
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
        score1=score_bet_in.team1.score,
        score2=score_bet_in.team2.score,
    )

    set_recomputation_flag(db, score_bet_in.team1.id, user.id)
    set_recomputation_flag(db, score_bet_in.team2.id, user.id)

    db.add(score_bet)
    db.commit()
    db.refresh(score_bet)

    return send_response(score_bet, locked=is_locked(user.name, settings.lock_datetime), lang=lang)


@router.get("/{bet_id}")
def retrieve_score_bet_by_id(
    bet_id: UUID4,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[UserModel, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[ScoreBetResponse]:
    score_bet = (
        db.query(ScoreBetModel)
        .join(ScoreBetModel.match)
        .filter(and_(MatchModel.user_id == user.id, ScoreBetModel.id == bet_id))
        .first()
    )

    if not score_bet:
        raise BetNotFound(bet_id)

    return send_response(score_bet, locked=is_locked(user.name, settings.lock_datetime), lang=lang)


@router.patch("/{bet_id}")
def modify_score_bet(
    bet_id: UUID4,
    modify_score_bet_in: ModifyScoreBetIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[UserModel, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[ScoreBetResponse]:
    if is_locked(user.name, settings.lock_datetime):
        raise LockedScoreBet

    score_bet = (
        db.query(ScoreBetModel)
        .join(ScoreBetModel.match)
        .filter(and_(MatchModel.user_id == user.id, ScoreBetModel.id == bet_id))
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
                raise TeamNotFound(modify_score_bet_in.team1.id) from integrity_error

        if "score" in modify_score_bet_in.team1.model_fields_set:
            score_bet.score1 = modify_score_bet_in.team1.score

    if modify_score_bet_in.team2 is not None:
        if "id" in modify_score_bet_in.team2.model_fields_set:
            score_bet.match.team2_id = modify_score_bet_in.team2.id

            try:
                db.flush()
            except IntegrityError as integrity_error:
                db.rollback()
                raise TeamNotFound(modify_score_bet_in.team2.id) from integrity_error

        if "score" in modify_score_bet_in.team2.model_fields_set:
            score_bet.score2 = modify_score_bet_in.team2.score

    set_recomputation_flag(db, score_bet.match.team1_id, user.id)
    set_recomputation_flag(db, score_bet.match.team2_id, user.id)

    db.commit()

    return send_response(score_bet, locked=is_locked(user.name, settings.lock_datetime), lang=lang)


@router.delete("/{bet_id}")
def delete_score_bet_by_id(
    bet_id: UUID4,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[UserModel, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[ScoreBetResponse]:
    if is_locked(user.name, settings.lock_datetime):
        raise LockedScoreBet

    score_bet = (
        db.query(ScoreBetModel)
        .join(ScoreBetModel.match)
        .filter(and_(MatchModel.user_id == user.id, ScoreBetModel.id == bet_id))
        .first()
    )

    if not score_bet:
        raise BetNotFound(bet_id)

    response = send_response(
        score_bet,
        locked=is_locked(user.name, settings.lock_datetime),
        lang=lang,
    )

    set_recomputation_flag(db, score_bet.match.team1_id, user.id)
    set_recomputation_flag(db, score_bet.match.team2_id, user.id)

    db.delete(score_bet)
    db.commit()

    return response
