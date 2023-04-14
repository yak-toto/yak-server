from typing import List, Optional

from pydantic import UUID4, BaseModel

from .generic import PositiveOrZeroInt


class FlagOut(BaseModel):
    url: str

    class Config:
        orm_mode = True


class TeamIn(BaseModel):
    id: UUID4
    score: Optional[PositiveOrZeroInt]


class TeamOut(BaseModel):
    id: UUID4
    code: str
    description: str
    flag: FlagOut

    class Config:
        orm_mode = True


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
