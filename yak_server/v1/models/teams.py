from typing import TYPE_CHECKING, Optional

from pydantic import UUID4, BaseModel, NonNegativeInt

from yak_server.helpers.language import Lang, get_language_description

if TYPE_CHECKING:
    from yak_server.database.models import TeamModel


class FlagOut(BaseModel):
    url: str


class TeamIn(BaseModel):
    id: UUID4
    score: Optional[NonNegativeInt] = None


class TeamOut(BaseModel):
    id: UUID4
    code: str
    description: str
    flag: FlagOut

    @classmethod
    def from_instance(cls, team: "TeamModel", *, lang: Lang) -> "TeamOut":
        return cls(
            id=team.id,
            code=team.code,
            description=get_language_description(team, lang),
            flag=FlagOut(url=team.flag_url),
        )


class AllTeamsResponse(BaseModel):
    teams: list[TeamOut]


class OneTeamResponse(BaseModel):
    team: TeamOut


class TeamWithWonOut(BaseModel):
    id: UUID4
    code: str
    description: str
    flag: FlagOut
    won: Optional[bool] = None


class TeamWithScoreOut(BaseModel):
    id: UUID4
    code: str
    description: str
    flag: FlagOut
    score: Optional[NonNegativeInt] = None


class TeamModifyScoreBetIn(BaseModel):
    id: Optional[UUID4] = None
    score: Optional[NonNegativeInt] = None


class TeamModifyBinaryBetIn(BaseModel):
    id: Optional[UUID4] = None
