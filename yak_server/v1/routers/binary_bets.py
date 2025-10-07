import logging
from typing import Annotated

import pendulum
from fastapi import APIRouter, Depends, status
from pydantic import UUID4
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from yak_server.database.models import BinaryBetModel, GroupModel, MatchModel, UserModel
from yak_server.helpers.bet_locking import is_locked
from yak_server.helpers.database import get_db
from yak_server.helpers.language import DEFAULT_LANGUAGE, Lang, get_language_description
from yak_server.helpers.logging_helpers import modify_binary_bet_successfully
from yak_server.helpers.settings import get_lock_datetime
from yak_server.v1.helpers.auth import require_user
from yak_server.v1.helpers.errors import BetNotFound, LockedBinaryBet, TeamNotFound
from yak_server.v1.models.binary_bets import BinaryBetOut, BinaryBetResponse, ModifyBinaryBetIn
from yak_server.v1.models.generic import ErrorOut, GenericOut, ValidationErrorOut
from yak_server.v1.models.groups import GroupOut
from yak_server.v1.models.phases import PhaseOut
from yak_server.v1.models.teams import FlagOut, TeamWithWonOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/binary_bets", tags=["binary_bets"])


def send_response(
    binary_bet: BinaryBetModel,
    *,
    locked: bool,
    lang: Lang,
) -> GenericOut[BinaryBetResponse]:
    return GenericOut(
        result=BinaryBetResponse(
            phase=PhaseOut.from_instance(binary_bet.match.group.phase, lang=lang),
            group=GroupOut.from_instance(binary_bet.match.group, lang=lang),
            binary_bet=BinaryBetOut(
                id=binary_bet.id,
                locked=locked,
                team1=(
                    TeamWithWonOut(
                        id=binary_bet.match.team1.id,
                        code=binary_bet.match.team1.code,
                        description=get_language_description(binary_bet.match.team1, lang),
                        flag=FlagOut(url=binary_bet.match.team1.flag_url),
                        won=binary_bet.bet_from_is_one_won()[0],
                    )
                    if binary_bet.match.team1 is not None
                    else None
                ),
                team2=(
                    TeamWithWonOut(
                        id=binary_bet.match.team2.id,
                        code=binary_bet.match.team2.code,
                        description=get_language_description(binary_bet.match.team2, lang),
                        flag=FlagOut(url=binary_bet.match.team2.flag_url),
                        won=binary_bet.bet_from_is_one_won()[1],
                    )
                    if binary_bet.match.team2 is not None
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
def retrieve_binary_bet_by_id(
    bet_id: UUID4,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[UserModel, Depends(require_user)],
    lock_datetime: Annotated[pendulum.DateTime, Depends(get_lock_datetime)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[BinaryBetResponse]:
    binary_bet = (
        db.query(BinaryBetModel)
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

    return send_response(binary_bet, locked=is_locked(user, lock_datetime), lang=lang)


@router.patch(
    "/{bet_id}",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut},
    },
)
def modify_binary_bet_by_id(
    bet_id: UUID4,
    modify_binary_bet_in: ModifyBinaryBetIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[UserModel, Depends(require_user)],
    lock_datetime: Annotated[pendulum.DateTime, Depends(get_lock_datetime)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[BinaryBetResponse]:
    if is_locked(user, lock_datetime):
        raise LockedBinaryBet

    binary_bet = (
        db.query(BinaryBetModel)
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

        try:
            db.flush()
        except IntegrityError as integrity_error:
            db.rollback()
            # team1.id is not None due to: "id" in modify_binary_bet_in.team1.model_fields_set
            # being true
            raise TeamNotFound(modify_binary_bet_in.team1.id) from integrity_error  # type: ignore[arg-type]

    if (
        modify_binary_bet_in.team2 is not None
        and "id" in modify_binary_bet_in.team2.model_fields_set
    ):
        binary_bet.match.team2_id = modify_binary_bet_in.team2.id

        try:
            db.flush()
        except IntegrityError as integrity_error:
            db.rollback()
            # team2.id is not None due to: "id" in modify_binary_bet_in.team2.model_fields_set
            # being true
            raise TeamNotFound(modify_binary_bet_in.team2.id) from integrity_error  # type: ignore[arg-type]

    db.commit()
    db.refresh(binary_bet)

    return send_response(binary_bet, locked=is_locked(user, lock_datetime), lang=lang)
