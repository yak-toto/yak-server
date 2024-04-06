import sys
from typing import TYPE_CHECKING, Dict, Tuple, Union

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    UserModel,
)
from yak_server.helpers.bet_locking import is_locked
from yak_server.helpers.database import get_db
from yak_server.helpers.language import DEFAULT_LANGUAGE, Lang
from yak_server.helpers.settings import Settings, get_settings
from yak_server.v1.helpers.auth import get_current_user

from .models import BinaryBetOut, GenericOut, GroupOut, PhaseOut, RetrieveAllBetsOut, ScoreBetOut

if TYPE_CHECKING:
    import uuid

router = APIRouter()


@router.post("/signupUser")
def signup(request: Request) -> None:
    return RedirectResponse(request.url_for("signup"))


@router.post("/loginUser")
def login(request: Request) -> None:
    return RedirectResponse(request.url_for("login"))


@router.post("/retrieveAllBets")
def retrieve_all_bets(
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[RetrieveAllBetsOut]:
    locked = is_locked(user.name, settings.lock_datetime)

    response = RetrieveAllBetsOut(phases=[])

    response_result: Dict[
        Tuple["uuid.UUID", "uuid.UUID", "uuid.UUID"], Union[BinaryBetModel, ScoreBetModel]
    ] = {}

    binary_bets = (
        db.query(BinaryBetModel)
        .join(BinaryBetModel.match)
        .filter(MatchModel.user_id == user.id)
        .join(MatchModel.group)
        .order_by(GroupModel.index, MatchModel.index)
    )

    for binary_bet in binary_bets:
        response_result[
            binary_bet.match.group.phase.id, binary_bet.match.group.id, binary_bet.id
        ] = binary_bet

    score_bets = (
        db.query(ScoreBetModel)
        .join(ScoreBetModel.match)
        .filter(MatchModel.user_id == user.id)
        .join(MatchModel.group)
        .order_by(GroupModel.index, MatchModel.index)
    )

    for score_bet in score_bets:
        response_result[score_bet.match.group.phase.id, score_bet.match.group.id, score_bet.id] = (
            score_bet
        )

    phases = db.query(PhaseModel).order_by(PhaseModel.index)

    for phase in phases:
        phase_response = PhaseOut.from_instance(phase, lang=lang)

        groups = db.query(GroupModel).order_by(GroupModel.index).filter_by(phase_id=phase.id)

        for group in groups:
            group_response = GroupOut.from_instance(group, lang=lang)

            for key, value in response_result.items():
                if key[0] == phase.id and key[1] == group.id:
                    if isinstance(value, BinaryBetModel):
                        group_response.binary_bets.append(
                            BinaryBetOut.from_instance(value, locked=locked, lang=lang)
                        )
                    else:
                        group_response.score_bets.append(
                            ScoreBetOut.from_instance(value, locked=locked, lang=lang)
                        )

            phase_response.groups.append(group_response)

        response.phases.append(phase_response)

    return GenericOut[RetrieveAllBetsOut](data=response)


@router.post("/modifyScoreBet")
def modify_score_bet():
    return {}


@router.post("/modifyBinaryBet")
def modify_binary_bet():
    return {}
