import logging

from fastapi import APIRouter, status
from pydantic import UUID4
from sqlalchemy.orm import selectinload

from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    MatchModel,
)
from yak_server.helpers.bet_locking import is_locked
from yak_server.helpers.database import SessionDep
from yak_server.helpers.language import DEFAULT_LANGUAGE, LangQuery
from yak_server.helpers.logging_helpers import modify_binary_bet_successfully
from yak_server.helpers.settings import LockDatetimeDep
from yak_server.v1.helpers.auth import CurrentUserDep
from yak_server.v1.helpers.errors import BetNotFound, LockedBinaryBet
from yak_server.v1.helpers.responses import error_responses
from yak_server.v1.helpers.teams import validate_team_id
from yak_server.v1.models.binary_bets import BinaryBetResponse, ModifyBinaryBetIn
from yak_server.v1.models.generic import GenericOut

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/binary_bets",
    tags=["binary_bets"],
    responses=error_responses(status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND),
)


@router.get("/{bet_id}")
def retrieve_binary_bet_by_id(
    bet_id: UUID4,
    db: SessionDep,
    user: CurrentUserDep,
    lock_datetime: LockDatetimeDep,
    lang: LangQuery = DEFAULT_LANGUAGE,
) -> GenericOut[BinaryBetResponse]:
    binary_bet = (
        db
        .query(BinaryBetModel)
        .options(
            selectinload(BinaryBetModel.match)
            .selectinload(MatchModel.group)
            .selectinload(GroupModel.phase),
            selectinload(BinaryBetModel.match).selectinload(MatchModel.group),
            selectinload(BinaryBetModel.match).selectinload(MatchModel.team1),
            selectinload(BinaryBetModel.match).selectinload(MatchModel.team2),
        )
        .join(BinaryBetModel.match)
        .where(MatchModel.user_id == user.id, BinaryBetModel.id == bet_id)
        .first()
    )

    if not binary_bet:
        raise BetNotFound(bet_id)

    return GenericOut(
        result=BinaryBetResponse.from_instance(
            binary_bet, locked=is_locked(user, lock_datetime), lang=lang
        ),
    )


@router.patch("/{bet_id}", responses=error_responses(status.HTTP_403_FORBIDDEN))
def modify_binary_bet_by_id(
    bet_id: UUID4,
    modify_binary_bet_in: ModifyBinaryBetIn,
    db: SessionDep,
    user: CurrentUserDep,
    lock_datetime: LockDatetimeDep,
    lang: LangQuery = DEFAULT_LANGUAGE,
) -> GenericOut[BinaryBetResponse]:
    if is_locked(user, lock_datetime):
        raise LockedBinaryBet

    binary_bet = (
        db
        .query(BinaryBetModel)
        .options(
            selectinload(BinaryBetModel.match)
            .selectinload(MatchModel.group)
            .selectinload(GroupModel.phase),
            selectinload(BinaryBetModel.match).selectinload(MatchModel.group),
            selectinload(BinaryBetModel.match).selectinload(MatchModel.team1),
            selectinload(BinaryBetModel.match).selectinload(MatchModel.team2),
        )
        .join(BinaryBetModel.match)
        .where(MatchModel.user_id == user.id, BinaryBetModel.id == bet_id)
        .first()
    )

    if not binary_bet:
        raise BetNotFound(bet_id)

    for team in (modify_binary_bet_in.team1, modify_binary_bet_in.team2):
        if team is not None and "id" in team.model_fields_set:
            validate_team_id(db, team.id)

    logger.info(
        modify_binary_bet_successfully(
            user.name,
            binary_bet,
            new_is_one_won=modify_binary_bet_in.is_one_won,
        ),
    )

    if "is_one_won" in modify_binary_bet_in.model_fields_set:
        binary_bet.is_one_won = modify_binary_bet_in.is_one_won

    if (
        modify_binary_bet_in.team1 is not None
        and "id" in modify_binary_bet_in.team1.model_fields_set
    ):
        binary_bet.match.team1_id = modify_binary_bet_in.team1.id

    if (
        modify_binary_bet_in.team2 is not None
        and "id" in modify_binary_bet_in.team2.model_fields_set
    ):
        binary_bet.match.team2_id = modify_binary_bet_in.team2.id

    db.commit()
    db.refresh(binary_bet)

    return GenericOut(
        result=BinaryBetResponse.from_instance(
            binary_bet, locked=is_locked(user, lock_datetime), lang=lang
        ),
    )
