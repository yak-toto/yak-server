from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import FileResponse

from yak_server.helpers.language import DEFAULT_LANGUAGE, Lang, get_language_description
from yak_server.helpers.settings import CommonSettings, Settings, get_common_settings, get_settings
from yak_server.v1.models.competition import CompetitionOut, LogoOut
from yak_server.v1.models.generic import ErrorOut, GenericOut, ValidationErrorOut

router = APIRouter(prefix="/competition", tags=["competition"])


@router.get(
    "",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut},
    },
)
def get_competition(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    common_settings: Annotated[CommonSettings, Depends(get_common_settings)],
    lang: Lang = DEFAULT_LANGUAGE,
) -> GenericOut[CompetitionOut]:
    return GenericOut(
        result=CompetitionOut(
            code=settings.competition,
            description=get_language_description(common_settings.competition, lang),
            logo=LogoOut(url=request.url_for("get_competition_logo").path),
        )
    )


@router.get(
    "/logo",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut},
    },
)
def get_competition_logo(settings: Annotated[Settings, Depends(get_settings)]) -> FileResponse:
    return FileResponse(
        f"{settings.data_folder}/logo.svg",
        headers={"Cache-Control": "public, max-age=86400"},
    )
