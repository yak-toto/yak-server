import logging

from fastapi import APIRouter, status
from pydantic import UUID4
from sqlalchemy.orm import selectinload

from yak_server.database.models import GroupModel, MatchModel, ScoreBetModel
from yak_server.helpers.bet_locking import is_locked
from yak_server.helpers.database import SessionDep
from yak_server.helpers.group_position import set_recomputation_flag
from yak_server.helpers.language import DEFAULT_LANGUAGE, LangQuery
from yak_server.helpers.logging_helpers import modify_score_bet_successfully
from yak_server.helpers.settings import LockDatetimeDep
from yak_server.v1.helpers.auth import CurrentUserDep
from yak_server.v1.helpers.errors import BetNotFound, LockedScoreBet
from yak_server.v1.helpers.responses import error_responses
from yak_server.v1.helpers.teams import validate_team_id
from yak_server.v1.models.generic import GenericOut
from yak_server.v1.models.score_bets import (
    BulkModifyScoreBetItem,
    ModifyScoreBetIn,
    ScoreBetResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/score_bets",
    tags=["score_bets"],
    responses=error_responses(status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND),
)


@router.patch("", responses=error_responses(status.HTTP_403_FORBIDDEN))
def bulk_modify_score_bets(  # ruff:ignore[complex-structure]
    score_bets_in: list[BulkModifyScoreBetItem],
    db: SessionDep,
    user: CurrentUserDep,
    lock_datetime: LockDatetimeDep,
    lang: LangQuery = DEFAULT_LANGUAGE,
) -> GenericOut[list[ScoreBetResponse]]:
    if is_locked(user, lock_datetime):
        raise LockedScoreBet

    requested_ids = [item.id for item in score_bets_in]

    score_bets = (
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
        .where(MatchModel.user_id == user.id, ScoreBetModel.id.in_(requested_ids))
        .with_for_update()
        .all()
    )

    score_bets_by_id = {sb.id: sb for sb in score_bets}
    missing = [rid for rid in requested_ids if rid not in score_bets_by_id]
    if missing:
        raise BetNotFound(missing[0])

    for item in score_bets_in:
        validate_team_id(db, getattr(item.team1, "id", None))
        validate_team_id(db, getattr(item.team2, "id", None))

    team_ids: set[UUID4 | None] = set()

    for item in score_bets_in:
        score_bet = score_bets_by_id[item.id]

        logger.info(
            modify_score_bet_successfully(
                user.name,
                score_bet,
                item.team1.score if item.team1 else None,
                item.team2.score if item.team2 else None,
            ),
        )

        if item.team1 is not None:
            if "id" in item.team1.model_fields_set:
                score_bet.match.team1_id = item.team1.id
            if "score" in item.team1.model_fields_set:
                score_bet.score1 = item.team1.score

        if item.team2 is not None:
            if "id" in item.team2.model_fields_set:
                score_bet.match.team2_id = item.team2.id
            if "score" in item.team2.model_fields_set:
                score_bet.score2 = item.team2.score

        team_ids.add(score_bet.match.team1_id)
        team_ids.add(score_bet.match.team2_id)

    db.flush()

    for team_id in team_ids:
        set_recomputation_flag(db, team_id, user.id)

    db.commit()
    for score_bet in score_bets:
        db.refresh(score_bet)

    locked = is_locked(user, lock_datetime)
    return GenericOut(
        result=[
            ScoreBetResponse.from_instance(score_bets_by_id[rid], locked=locked, lang=lang)
            for rid in requested_ids
        ],
    )


@router.get("/{bet_id}")
def retrieve_score_bet_by_id(
    bet_id: UUID4,
    db: SessionDep,
    user: CurrentUserDep,
    lock_datetime: LockDatetimeDep,
    lang: LangQuery = DEFAULT_LANGUAGE,
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

    return GenericOut(
        result=ScoreBetResponse.from_instance(
            score_bet, locked=is_locked(user, lock_datetime), lang=lang
        ),
    )


@router.patch("/{bet_id}", responses=error_responses(status.HTTP_403_FORBIDDEN))
def modify_score_bet(
    bet_id: UUID4,
    modify_score_bet_in: ModifyScoreBetIn,
    db: SessionDep,
    user: CurrentUserDep,
    lock_datetime: LockDatetimeDep,
    lang: LangQuery = DEFAULT_LANGUAGE,
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

    for team in (modify_score_bet_in.team1, modify_score_bet_in.team2):
        if team is not None and "id" in team.model_fields_set:
            validate_team_id(db, team.id)

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

        if "score" in modify_score_bet_in.team1.model_fields_set:
            score_bet.score1 = modify_score_bet_in.team1.score

    if modify_score_bet_in.team2 is not None:
        if "id" in modify_score_bet_in.team2.model_fields_set:
            score_bet.match.team2_id = modify_score_bet_in.team2.id

        if "score" in modify_score_bet_in.team2.model_fields_set:
            score_bet.score2 = modify_score_bet_in.team2.score

    set_recomputation_flag(db, score_bet.match.team1_id, user.id)
    set_recomputation_flag(db, score_bet.match.team2_id, user.id)

    db.commit()
    db.refresh(score_bet)

    return GenericOut(
        result=ScoreBetResponse.from_instance(
            score_bet, locked=is_locked(user, lock_datetime), lang=lang
        ),
    )
