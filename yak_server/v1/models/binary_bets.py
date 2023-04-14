from typing import Optional

from pydantic import UUID4, BaseModel, PositiveInt

from .groups import GroupIn, GroupOut
from .phases import PhaseOut
from .teams import TeamIn, TeamModifyBinaryBetIn, TeamWithWonOut


class BinaryBetIn(BaseModel):
    is_one_won: Optional[bool]
    index: PositiveInt
    team1: TeamIn
    team2: TeamIn
    group: GroupIn


class BinaryBetOut(BaseModel):
    id: UUID4
    index: PositiveInt
    locked: bool
    team1: Optional[TeamWithWonOut]
    team2: Optional[TeamWithWonOut]


class Group(BaseModel):
    id: UUID4


class BinaryBetWithGroupIdOut(BaseModel):
    id: UUID4
    index: PositiveInt
    locked: bool
    group: Group
    team1: Optional[TeamWithWonOut]
    team2: Optional[TeamWithWonOut]


class BinaryBetResponse(BaseModel):
    phase: PhaseOut
    group: GroupOut
    binary_bet: BinaryBetOut


class ModifyBinaryBetIn(BaseModel):
    is_one_won: Optional[bool]
    team1: Optional[TeamModifyBinaryBetIn]
    team2: Optional[TeamModifyBinaryBetIn]

    class Config:
        extra = "forbid"
