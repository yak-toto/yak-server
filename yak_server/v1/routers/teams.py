from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse
from pydantic import UUID4
from sqlalchemy.orm import Session

from yak_server.database.models import TeamModel
from yak_server.helpers.database import get_db
from yak_server.helpers.format import is_iso_3166_1_alpha_2_code, is_uuid4
from yak_server.helpers.language import DEFAULT_LANGUAGE, Lang
from yak_server.v1.helpers.errors import InvalidTeamId, TeamNotFound
from yak_server.v1.models.generic import ErrorOut, GenericOut, ValidationErrorOut
from yak_server.v1.models.teams import AllTeamsResponse, OneTeamResponse, TeamOut

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get(
    "/",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut},
    },
)
def retrieve_all_teams(
    db: Annotated[Session, Depends(get_db)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[AllTeamsResponse]:
    return GenericOut(
        result=AllTeamsResponse(
            teams=[TeamOut.from_instance(team, lang=lang) for team in db.query(TeamModel).all()],
        ),
    )


@router.get(
    "/{team_id}",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut},
    },
)
def retrieve_team_by_id(
    team_id: str,
    db: Annotated[Session, Depends(get_db)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[OneTeamResponse]:
    if is_uuid4(team_id):
        team = db.query(TeamModel).filter_by(id=team_id).first()
    elif is_iso_3166_1_alpha_2_code(team_id):
        team = db.query(TeamModel).filter_by(code=team_id).first()
    else:
        raise InvalidTeamId(team_id)

    if not team:
        raise TeamNotFound(team_id)

    return GenericOut(result=OneTeamResponse(team=TeamOut.from_instance(team, lang=lang)))


@router.get(
    "/{team_id}/flag",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut},
    },
)
def retrieve_team_flag_by_id(
    team_id: UUID4,
    db: Annotated[Session, Depends(get_db)],
) -> RedirectResponse:
    team = db.query(TeamModel).filter_by(id=team_id).first()

    if not team:
        raise TeamNotFound(team_id)

    return RedirectResponse(team.internal_flag_url)
