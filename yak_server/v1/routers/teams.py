from fastapi import APIRouter, status
from fastapi.responses import FileResponse
from pydantic import UUID4

from yak_server.database.models import TeamModel
from yak_server.helpers.database import SessionDep
from yak_server.helpers.language import DEFAULT_LANGUAGE, LangQuery
from yak_server.helpers.settings import SettingsDep
from yak_server.v1.helpers.errors import TeamFlagNotFound, TeamNotFound
from yak_server.v1.helpers.responses import error_responses
from yak_server.v1.models.generic import GenericOut
from yak_server.v1.models.teams import AllTeamsResponse, OneTeamResponse, TeamOut

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("")
def retrieve_all_teams(
    db: SessionDep,
    lang: LangQuery = DEFAULT_LANGUAGE,
) -> GenericOut[AllTeamsResponse]:
    return GenericOut(
        result=AllTeamsResponse(
            teams=[TeamOut.from_instance(team, lang=lang) for team in db.query(TeamModel).all()],
        ),
    )


@router.get("/{team_id}", responses=error_responses(status.HTTP_404_NOT_FOUND))
def retrieve_team_by_id(
    team_id: UUID4,
    db: SessionDep,
    lang: LangQuery = DEFAULT_LANGUAGE,
) -> GenericOut[OneTeamResponse]:
    team = db.query(TeamModel).filter_by(id=team_id).first()

    if not team:
        raise TeamNotFound(team_id)

    return GenericOut(result=OneTeamResponse(team=TeamOut.from_instance(team, lang=lang)))


@router.get("/{team_id}/flag", responses=error_responses(status.HTTP_404_NOT_FOUND))
def retrieve_team_flag_by_id(
    team_id: UUID4,
    db: SessionDep,
    settings: SettingsDep,
) -> FileResponse:
    team = db.query(TeamModel).filter_by(id=team_id).first()

    if not team:
        raise TeamNotFound(team_id)

    flag_path = settings.data_folder.parent / "flags" / team.internal_flag_path

    if not flag_path.is_file():
        raise TeamFlagNotFound(team_id)

    return FileResponse(flag_path, headers={"Cache-Control": "public, max-age=86400"})
