from typing import TYPE_CHECKING, List, Optional

from pydantic import UUID4, BaseModel

from .generic import PositiveOrZeroInt

if TYPE_CHECKING:
    from yak_server.database.models import TeamModel


class FlagOut(BaseModel):
    url: str


class TeamIn(BaseModel):
    id: UUID4
    score: Optional[PositiveOrZeroInt]


class TeamOut(BaseModel):
    id: UUID4
    code: str
    description: str
    flag: FlagOut

    @classmethod
    def from_instance(cls, team: "TeamModel") -> "TeamOut":
        return cls(
            id=team.id,
            code=team.code,
            description=team.description_fr,
            flag=FlagOut(url=team.flag_url),
        )


class AllTeamsResponse(BaseModel):
    teams: List[TeamOut]


class OneTeamResponse(BaseModel):
    team: TeamOut


class TeamWithWonOut(BaseModel):
    id: UUID4
    code: str
    description: str
    flag: FlagOut
    won: Optional[bool]


class TeamWithScoreOut(BaseModel):
    id: UUID4
    code: str
    description: str
    flag: FlagOut
    score: Optional[PositiveOrZeroInt]


class TeamModifyScoreBetIn(BaseModel):
    score: Optional[PositiveOrZeroInt]


class TeamModifyBinaryBetIn(BaseModel):
    id: Optional[UUID4]
