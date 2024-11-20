from pydantic import BaseModel

from .binary_bets import BinaryBetOut, BinaryBetWithGroupIdOut
from .group_rank import GroupPositionOut
from .groups import GroupOut, GroupWithPhaseIdOut
from .phases import PhaseOut
from .score_bets import ScoreBetOut, ScoreBetWithGroupIdOut


class AllBetsResponse(BaseModel):
    phases: list[PhaseOut]
    groups: list[GroupWithPhaseIdOut]
    score_bets: list[ScoreBetWithGroupIdOut]
    binary_bets: list[BinaryBetWithGroupIdOut]


class BetsByPhaseCodeResponse(BaseModel):
    phase: PhaseOut
    groups: list[GroupOut]
    score_bets: list[ScoreBetWithGroupIdOut]
    binary_bets: list[BinaryBetWithGroupIdOut]


class BetsByGroupCodeResponse(BaseModel):
    phase: PhaseOut
    group: GroupOut
    score_bets: list[ScoreBetOut]
    binary_bets: list[BinaryBetOut]


class GroupRankResponse(BaseModel):
    phase: PhaseOut
    group: GroupOut
    group_rank: list[GroupPositionOut]
