from pydantic import UUID4, BaseModel, PositiveInt

from .groups import GroupIn, GroupOut
from .phases import PhaseOut
from .teams import TeamIn, TeamModifyScoreBetIn, TeamWithScoreOut


class ScoreBetIn(BaseModel):
    index: PositiveInt
    team1: TeamIn
    team2: TeamIn
    group: GroupIn


class ScoreBetOut(BaseModel):
    id: UUID4
    index: PositiveInt
    locked: bool
    team1: TeamWithScoreOut
    team2: TeamWithScoreOut


class Group(BaseModel):
    id: UUID4


class ScoreBetWithGroupIdOut(BaseModel):
    id: UUID4
    index: PositiveInt
    locked: bool
    group: Group
    team1: TeamWithScoreOut
    team2: TeamWithScoreOut


class ScoreBetResponse(BaseModel):
    phase: PhaseOut
    group: GroupOut
    score_bet: ScoreBetOut


class ModifyScoreBetIn(BaseModel):
    team1: TeamModifyScoreBetIn
    team2: TeamModifyScoreBetIn
