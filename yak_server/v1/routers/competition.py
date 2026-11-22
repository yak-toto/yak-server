from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from yak_server.helpers.language import DEFAULT_LANGUAGE, LangQuery, get_language_description
from yak_server.helpers.settings import CommonSettingsDep, SettingsDep
from yak_server.v1.models.competition import CompetitionOut, LogoOut
from yak_server.v1.models.generic import GenericOut

router = APIRouter(prefix="/competition", tags=["competition"])


@router.get("")
def get_competition(
    request: Request,
    settings: SettingsDep,
    common_settings: CommonSettingsDep,
    lang: LangQuery = DEFAULT_LANGUAGE,
) -> GenericOut[CompetitionOut]:
    return GenericOut(
        result=CompetitionOut(
            code=settings.competition,
            description=get_language_description(common_settings.competition, lang),
            logo=LogoOut(url=request.url_for("get_competition_logo").path),
        )
    )


@router.get("/logo")
def get_competition_logo(settings: SettingsDep) -> FileResponse:
    return FileResponse(
        f"{settings.data_folder}/logo.svg",
        headers={"Cache-Control": "public, max-age=86400"},
    )
