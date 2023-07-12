from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError

from yak_server.config_file import Settings, get_settings
from yak_server.database.models import (
    BinaryBetModel,
    MatchModel,
    UserModel,
)
from yak_server.helpers.bet_locking import is_locked
from yak_server.helpers.language import DEFAULT_LANGUAGE, Lang, get_language_description
from yak_server.helpers.logging import modify_binary_bet_successfully
from yak_server.v1.helpers.auth import get_current_user
from yak_server.v1.helpers.database import get_db
from yak_server.v1.helpers.errors import (
    BetNotFound,
    GroupNotFound,
    LockedBinaryBet,
    TeamNotFound,
)
from yak_server.v1.models.binary_bets import (
    BinaryBetIn,
    BinaryBetOut,
    BinaryBetResponse,
    ModifyBinaryBetIn,
    TeamWithWonOut,
)
from yak_server.v1.models.generic import GenericOut
from yak_server.v1.models.groups import GroupOut
from yak_server.v1.models.phases import PhaseOut
from yak_server.v1.models.teams import FlagOut

if TYPE_CHECKING:
    from pydantic import UUID4
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/binary_bets",
    tags=["binary_bets"],
)


def send_response(
    binary_bet: BinaryBetModel,
    locked: bool,
    lang: Lang,
) -> GenericOut[BinaryBetResponse]:
    return GenericOut(
        result=BinaryBetResponse(
            phase=PhaseOut.from_instance(binary_bet.match.group.phase, lang),
            group=GroupOut.from_instance(binary_bet.match.group, lang),
            binary_bet=BinaryBetOut(
                id=binary_bet.id,
                locked=locked,
                team1=TeamWithWonOut(
                    id=binary_bet.match.team1.id,
                    code=binary_bet.match.team1.code,
                    description=get_language_description(binary_bet.match.team1, lang),
                    flag=FlagOut(url=binary_bet.match.team1.flag_url),
                    won=binary_bet.bet_from_is_one_won()[0],
                )
                if binary_bet.match.team1
                else None,
                team2=TeamWithWonOut(
                    id=binary_bet.match.team2.id,
                    code=binary_bet.match.team2.code,
                    description=get_language_description(binary_bet.match.team2, lang),
                    flag=FlagOut(url=binary_bet.match.team2.flag_url),
                    won=binary_bet.bet_from_is_one_won()[1],
                )
                if binary_bet.match.team2
                else None,
            ),
        ),
    )


@router.post("/")
def create_binary_bet(
    binary_bet_in: BinaryBetIn,
    lang: Lang = DEFAULT_LANGUAGE,
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> GenericOut[BinaryBetResponse]:
    if is_locked(user.name, settings.lock_datetime):
        raise LockedBinaryBet

    match = MatchModel(
        team1_id=binary_bet_in.team1.id,
        team2_id=binary_bet_in.team2.id,
        index=binary_bet_in.index,
        group_id=binary_bet_in.group.id,
    )

    db.add(match)
    try:
        db.flush()
    except IntegrityError as integrity_error:
        db.rollback()
        if "FOREIGN KEY (`team1_id`)" in str(integrity_error):
            raise TeamNotFound(team_id=binary_bet_in.team1.id) from integrity_error

        if "FOREIGN KEY (`team2_id`)" in str(integrity_error):
            raise TeamNotFound(team_id=binary_bet_in.team2.id) from integrity_error

        raise GroupNotFound(group_id=binary_bet_in.group.id) from integrity_error

    binary_bet = BinaryBetModel(
        match_id=match.id,
        user_id=user.id,
        is_one_won=binary_bet_in.is_one_won,
    )

    db.add(binary_bet)
    db.commit()
    db.refresh(binary_bet)

    return send_response(binary_bet, is_locked(user.name, settings.lock_datetime), lang)


@router.get("/{bet_id}")
def retrieve_binary_bet_by_id(
    bet_id: UUID4,
    lang: Lang = DEFAULT_LANGUAGE,
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> GenericOut[BinaryBetResponse]:
    binary_bet = db.query(BinaryBetModel).filter_by(user_id=user.id, id=str(bet_id)).first()

    if not binary_bet:
        raise BetNotFound(bet_id)

    return send_response(binary_bet, is_locked(user.name, settings.lock_datetime), lang)


@router.patch("/{bet_id}")
def modify_binary_bet_by_id(
    bet_id: UUID4,
    modify_binary_bet_in: ModifyBinaryBetIn,
    lang: Lang = DEFAULT_LANGUAGE,
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> GenericOut[BinaryBetResponse]:
    if is_locked(user.name, settings.lock_datetime):
        raise LockedBinaryBet

    binary_bet = db.query(BinaryBetModel).filter_by(user_id=user.id, id=str(bet_id)).first()

    if not binary_bet:
        raise BetNotFound(bet_id)

    logger.info(
        modify_binary_bet_successfully(user.name, binary_bet, modify_binary_bet_in.is_one_won),
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
            raise TeamNotFound(modify_binary_bet_in.team1.id) from integrity_error

    if (
        modify_binary_bet_in.team2 is not None
        and "id" in modify_binary_bet_in.team2.model_fields_set
    ):
        binary_bet.match.team2_id = modify_binary_bet_in.team2.id

        try:
            db.flush()
        except IntegrityError as integrity_error:
            db.rollback()
            raise TeamNotFound(modify_binary_bet_in.team2.id) from integrity_error

    db.commit()

    return send_response(binary_bet, is_locked(user.name, settings.lock_datetime), lang)


@router.delete("/{bet_id}")
def delete_binary_bet_by_id(
    bet_id: UUID4,
    lang: Lang = DEFAULT_LANGUAGE,
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> GenericOut[BinaryBetResponse]:
    if is_locked(user.name, settings.lock_datetime):
        raise LockedBinaryBet

    binary_bet = db.query(BinaryBetModel).filter_by(user_id=user.id, id=str(bet_id)).first()

    if not binary_bet:
        raise BetNotFound(bet_id)

    response = send_response(binary_bet, is_locked(user.name, settings.lock_datetime), lang)

    db.delete(binary_bet)
    db.commit()

    return response
