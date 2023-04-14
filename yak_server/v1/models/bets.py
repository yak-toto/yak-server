from typing import List

from pydantic import BaseModel

from .binary_bets import BinaryBetOut, BinaryBetWithGroupIdOut
from .group_rank import GroupPositionOut
from .groups import GroupOut, GroupWithPhaseIdOut
from .phases import PhaseOut
from .score_bets import ScoreBetOut, ScoreBetWithGroupIdOut


class AllBetsResponse(BaseModel):
    phases: List[PhaseOut]
    groups: List[GroupWithPhaseIdOut]
    score_bets: List[ScoreBetWithGroupIdOut]
    binary_bets: List[BinaryBetWithGroupIdOut]


class BetsByPhaseCodeResponse(BaseModel):
    phase: PhaseOut
    groups: List[GroupOut]
    score_bets: List[ScoreBetWithGroupIdOut]
    binary_bets: List[BinaryBetWithGroupIdOut]


class BetsByGroupCodeResponse(BaseModel):
    phase: PhaseOut
    group: GroupOut
    score_bets: List[ScoreBetOut]
    binary_bets: List[BinaryBetOut]


class GroupRankResponse(BaseModel):
    phase: PhaseOut
    group: GroupOut
    group_rank: List[GroupPositionOut]
