from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import UUID4, BaseModel, ConfigDict, PositiveInt

from yak_server.helpers.language import Lang, get_language_description

from .teams import FlagOut, TeamIn, TeamModifyScoreBetIn, TeamWithScoreOut

if TYPE_CHECKING:
    from yak_server.database.models import ScoreBetModel

    from .groups import GroupIn, GroupOut
    from .phases import PhaseOut


class ScoreBetIn(BaseModel):
    index: PositiveInt
    team1: TeamIn
    team2: TeamIn
    group: GroupIn


class ScoreBetOut(BaseModel):
    id: UUID4
    locked: bool
    team1: TeamWithScoreOut | None = None
    team2: TeamWithScoreOut | None = None

    @classmethod
    def from_instance(
        cls,
        score_bet: ScoreBetModel,
        *,
        locked: bool,
        lang: Lang,
    ) -> ScoreBetOut:
        return cls(
            id=score_bet.id,
            locked=locked,
            team1=(
                TeamWithScoreOut(
                    id=score_bet.match.team1.id,
                    code=score_bet.match.team1.code,
                    description=get_language_description(score_bet.match.team1, lang),
                    score=score_bet.score1,
                    flag=FlagOut(url=score_bet.match.team1.flag_url),
                )
                if score_bet.match.team1_id is not None
                else None
            ),
            team2=(
                TeamWithScoreOut(
                    id=score_bet.match.team2.id,
                    code=score_bet.match.team2.code,
                    description=get_language_description(score_bet.match.team2, lang),
                    score=score_bet.score2,
                    flag=FlagOut(url=score_bet.match.team2.flag_url),
                )
                if score_bet.match.team2_id is not None
                else None
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
    def from_instance(
        cls,
        score_bet: ScoreBetModel,
        *,
        locked: bool,
        lang: Lang,
    ) -> ScoreBetWithGroupIdOut:
        return cls(
            id=score_bet.id,
            locked=locked,
            group=Group(id=score_bet.match.group_id),
            team1=TeamWithScoreOut(
                id=score_bet.match.team1.id,
                code=score_bet.match.team1.code,
                description=get_language_description(score_bet.match.team1, lang),
                score=score_bet.score1,
                flag=FlagOut(url=score_bet.match.team1.flag_url),
            ),
            team2=TeamWithScoreOut(
                id=score_bet.match.team2.id,
                code=score_bet.match.team2.code,
                description=get_language_description(score_bet.match.team2, lang),
                score=score_bet.score2,
                flag=FlagOut(url=score_bet.match.team2.flag_url),
            ),
        )


class ScoreBetResponse(BaseModel):
    phase: PhaseOut
    group: GroupOut
    score_bet: ScoreBetOut


class ModifyScoreBetIn(BaseModel):
    team1: TeamModifyScoreBetIn | None = None
    team2: TeamModifyScoreBetIn | None = None

    model_config = ConfigDict(extra="forbid")
