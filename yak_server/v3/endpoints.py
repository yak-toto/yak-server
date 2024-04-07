import logging
from typing import Annotated
from uuid import UUID

import pendulum
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import and_
from sqlalchemy.orm import Session

from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    TeamModel,
    UserModel,
)
from yak_server.helpers.authentication import encode_bearer_token, get_current_user
from yak_server.helpers.bet_locking import is_locked
from yak_server.helpers.database import get_db
from yak_server.helpers.errors import BetNotFound, InvalidCredentials, TeamNotFound
from yak_server.helpers.language import DEFAULT_LANGUAGE, Lang
from yak_server.helpers.logging_helpers import logged_in_successfully
from yak_server.helpers.settings import Settings, get_settings

from .models import (
    BinaryBetOut,
    GenericOut,
    GroupOut,
    LoginIn,
    LoginOut,
    PhaseOut,
    RetrieveAllBetsOut,
    ScoreBetIn,
    ScoreBetOut,
)

logger = logging.getLogger(__name__)


router = APIRouter()


@router.post("/signupUser")
def signup(request: Request) -> None:
    return RedirectResponse(request.url_for("signup"))


@router.post("/loginUser")
def login(
    login_in: LoginIn,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    user = UserModel.authenticate(db, login_in.name, login_in.password)

    if not user:
        raise InvalidCredentials

    logger.info(logged_in_successfully(user.name))

    return GenericOut(
        data=LoginOut(
            id=user.id,
            name=user.name,
            token=encode_bearer_token(
                sub=user.id,
                expiration_time=pendulum.duration(seconds=settings.jwt_expiration_time),
                secret_key=settings.jwt_secret_key,
            ),
        ),
    )


@router.post("/retrieveAllBets")
def retrieve_all_bets(
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[RetrieveAllBetsOut]:
    locked = is_locked(user.name, settings.lock_datetime)

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

    response = RetrieveAllBetsOut(phases=[])

    for phase in phases:
        phase_response = PhaseOut.from_instance(phase, lang=lang)

        for group in groups.filter_by(phase_id=phase.id):
            group_response = GroupOut.from_instance(group, lang=lang)

            for score_bet in score_bets.filter_by(id=group.id):
                group_response.score_bets.append(
                    ScoreBetOut.from_instance(score_bet, locked=locked, lang=lang)
                )

            for binary_bet in binary_bets.filter_by(id=group.id):
                group_response.binary_bets.append(
                    BinaryBetOut.from_instance(binary_bet, locked=locked, lang=lang)
                )

            phase_response.groups.append(group_response)

        response.phases.append(phase_response)

    return GenericOut[RetrieveAllBetsOut](data=response)


@router.post("/modifyScoreBet")
def modify_score_bet(
    score_bet_in: ScoreBetIn,
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[ScoreBetOut]:
    locked = is_locked(user.name, settings.lock_datetime)

    score_bet = (
        db.query(ScoreBetModel)
        .join(ScoreBetModel.match)
        .filter(and_(ScoreBetModel.id == score_bet_in.id, MatchModel.user_id == user.id))
        .first()
    )

    if score_bet is None:
        raise BetNotFound(score_bet_in.id)

    if score_bet.match.team1_id == score_bet_in.team_id:
        score_bet.score1 = score_bet_in.score
    elif score_bet.match.team2_id == score_bet_in.team_id:
        score_bet.score2 = score_bet_in.score
    else:
        raise TeamNotFound(score_bet_in.team_id)

    return GenericOut[ScoreBetOut](
        data=ScoreBetOut.from_instance(score_bet, locked=locked, lang=lang)
    )


@router.post("/binary-bets/{binary_bet_id}/modifyWinner/{team_id}")
def modify_binary_bet_winner(
    binary_bet_id: UUID,
    team_id: UUID,
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[BinaryBetOut]:
    locked = is_locked(user.name, settings.lock_datetime)

    binary_bet = (
        db.query(BinaryBetModel)
        .join(BinaryBetModel.match)
        .filter(and_(BinaryBetModel.id == binary_bet_id, MatchModel.user_id == user.id))
        .first()
    )

    if binary_bet is None:
        raise BetNotFound(binary_bet_id)

    if binary_bet.match.team1_id == team_id:
        binary_bet.is_one_won = True
    elif binary_bet.match.team2_id == team_id:
        binary_bet.is_one_won = False
    else:
        raise TeamNotFound(team_id)

    db.commit()
    db.refresh(binary_bet)

    return GenericOut[BinaryBetOut](
        data=BinaryBetOut.from_instance(binary_bet, locked=locked, lang=lang)
    )


def modify_team_binary_bets(
    user: UserModel,
    binary_bet_id: UUID,
    team_id: UUID,
    db: Session,
    *,
    modify_team1: bool,
) -> BinaryBetModel:
    team = db.query(TeamModel).filter_by(id=team_id).first()

    if team is None:
        raise TeamNotFound(team_id)

    binary_bet = (
        db.query(BinaryBetModel)
        .join(BinaryBetModel.match)
        .filter(and_(BinaryBetModel.id == binary_bet_id, MatchModel.user_id == user.id))
        .first()
    )

    if binary_bet is None:
        raise BetNotFound(binary_bet_id)

    if modify_team1 is True:
        binary_bet.match.team1_id = team_id
    else:
        binary_bet.match.team2_id = team_id

    db.commit()
    db.refresh(binary_bet)

    return binary_bet


@router.post("/binary-bets/{binary_bet_id}/modifyTeam1/{team_id}")
def modify_binary_bet_team1(
    binary_bet_id: UUID,
    team_id: UUID,
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[BinaryBetOut]:
    locked = is_locked(user.name, settings.lock_datetime)

    binary_bet = modify_team_binary_bets(user, binary_bet_id, team_id, db, modify_team1=True)

    return GenericOut[BinaryBetOut](
        data=BinaryBetOut.from_instance(binary_bet, locked=locked, lang=lang)
    )


@router.post("/binary-bets/{binary_bet_id}/modifyTeam2/{team_id}")
def modify_binary_bet_team2(
    binary_bet_id: UUID,
    team_id: UUID,
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[BinaryBetOut]:
    locked = is_locked(user.name, settings.lock_datetime)

    binary_bet = modify_team_binary_bets(user, binary_bet_id, team_id, db, modify_team1=False)

    return GenericOut[BinaryBetOut](
        data=BinaryBetOut.from_instance(binary_bet, locked=locked, lang=lang)
    )
