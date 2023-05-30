from typing import TYPE_CHECKING

from pydantic import UUID4, BaseModel, PositiveInt

from .groups import GroupIn, GroupOut
from .phases import PhaseOut
from .teams import FlagOut, TeamIn, TeamModifyScoreBetIn, TeamWithScoreOut

if TYPE_CHECKING:
    from yak_server.database.models import ScoreBetModel


class ScoreBetIn(BaseModel):
    index: PositiveInt
    team1: TeamIn
    team2: TeamIn
    group: GroupIn


class ScoreBetOut(BaseModel):
    id: UUID4
    locked: bool
    team1: TeamWithScoreOut
    team2: TeamWithScoreOut

    @classmethod
    def from_instance(cls, score_bet: "ScoreBetModel", locked: bool) -> "ScoreBetOut":
        return cls(
            id=score_bet.id,
            locked=locked,
            team1=TeamWithScoreOut(
                id=score_bet.match.team1.id,
                code=score_bet.match.team1.code,
                description=score_bet.match.team1.description_fr,
                score=score_bet.score1,
                flag=FlagOut(url=score_bet.match.team1.flag_url),
            ),
            team2=TeamWithScoreOut(
                id=score_bet.match.team2.id,
                code=score_bet.match.team2.code,
                description=score_bet.match.team2.description_fr,
                score=score_bet.score2,
                flag=FlagOut(url=score_bet.match.team2.flag_url),
            ),
        )


class Group(BaseModel):
    id: UUID4


class ScoreBetWithGroupIdOut(BaseModel):
    id: UUID4
    locked: bool
    group: Group
    team1: TeamWithScoreOut
    team2: TeamWithScoreOut

    @classmethod
    def from_instance(cls, score_bet: "ScoreBetModel", locked: bool) -> "ScoreBetWithGroupIdOut":
        return cls(
            id=score_bet.id,
            locked=locked,
            group=Group(id=score_bet.match.group_id),
            team1=TeamWithScoreOut(
                id=score_bet.match.team1.id,
                code=score_bet.match.team1.code,
                description=score_bet.match.team1.description_fr,
                score=score_bet.score1,
                flag=FlagOut(url=score_bet.match.team1.flag_url),
            ),
            team2=TeamWithScoreOut(
                id=score_bet.match.team2.id,
                code=score_bet.match.team2.code,
                description=score_bet.match.team2.description_fr,
                score=score_bet.score2,
                flag=FlagOut(url=score_bet.match.team2.flag_url),
            ),
        )


class ScoreBetResponse(BaseModel):
    phase: PhaseOut
    group: GroupOut
    score_bet: ScoreBetOut


class ModifyScoreBetIn(BaseModel):
    team1: TeamModifyScoreBetIn
    team2: TeamModifyScoreBetIn
