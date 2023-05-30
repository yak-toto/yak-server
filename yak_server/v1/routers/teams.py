from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from pydantic import UUID4
from sqlalchemy.orm import Session

from yak_server.database.models import TeamModel
from yak_server.helpers.format import is_iso_3166_1_alpha_2_code, is_uuid4
from yak_server.v1.helpers.database import get_db
from yak_server.v1.helpers.errors import InvalidTeamId, TeamNotFound
from yak_server.v1.models.generic import GenericOut
from yak_server.v1.models.teams import AllTeamsResponse, OneTeamResponse, TeamOut

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/")
def retrieve_all_teams(
    db: Session = Depends(get_db),
) -> GenericOut[AllTeamsResponse]:
    return GenericOut(
        result=AllTeamsResponse(
            teams=[TeamOut.from_instance(team) for team in db.query(TeamModel).all()],
        ),
    )


@router.get("/{team_id}")
def retrieve_team_by_id(
    team_id: str,
    db: Session = Depends(get_db),
) -> GenericOut[OneTeamResponse]:
    if is_uuid4(team_id):
        team = db.query(TeamModel).filter_by(id=team_id).first()
    elif is_iso_3166_1_alpha_2_code(team_id):
        team = db.query(TeamModel).filter_by(code=team_id).first()
    else:
        raise InvalidTeamId(team_id)

    if not team:
        raise TeamNotFound(team_id)

    return GenericOut(result=OneTeamResponse(team=TeamOut.from_instance(team)))


@router.get("/{team_id}/flag")
def retrieve_team_flag_by_id(team_id: UUID4, db: Session = Depends(get_db)) -> RedirectResponse:
    team = db.query(TeamModel).filter_by(id=str(team_id)).first()

    if not team:
        raise TeamNotFound(team_id)

    return RedirectResponse(team.internal_flag_url)
