import uuid
from typing import TYPE_CHECKING, Generic, Optional, TypeVar

from pydantic import AliasGenerator, BaseModel, ConfigDict, NonNegativeInt
from pydantic.alias_generators import to_camel

from yak_server.helpers.language import Lang, get_language_description

if TYPE_CHECKING:
    from yak_server.database.models import BinaryBetModel, GroupModel, PhaseModel, ScoreBetModel

Data = TypeVar("Data")


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", alias_generator=AliasGenerator(serialization_alias=to_camel)
    )


class FlagOut(CustomBaseModel):
    url: str


class TeamWithWonOut(CustomBaseModel):
    id: uuid.UUID
    description: str
    flag: FlagOut
    won: Optional[bool] = None


class BinaryBetOut(CustomBaseModel):
    id: uuid.UUID
    locked: bool
    team1: Optional[TeamWithWonOut] = None
    team2: Optional[TeamWithWonOut] = None

    @classmethod
    def from_instance(
        cls,
        binary_bet: "BinaryBetModel",
        *,
        locked: bool,
        lang: "Lang",
    ) -> "BinaryBetOut":
        return cls(
            id=binary_bet.id,
            locked=locked,
            team1=(
                TeamWithWonOut(
                    id=binary_bet.match.team1.id,
                    description=get_language_description(binary_bet.match.team1, lang),
                    won=binary_bet.bet_from_is_one_won()[0],
                    flag=FlagOut(url=binary_bet.match.team1.flag_url),
                )
                if binary_bet.match.team1
                else None
            ),
            team2=(
                TeamWithWonOut(
                    id=binary_bet.match.team2.id,
                    description=get_language_description(binary_bet.match.team2, lang),
                    won=binary_bet.bet_from_is_one_won()[1],
                    flag=FlagOut(url=binary_bet.match.team2.flag_url),
                )
                if binary_bet.match.team2
                else None
            ),
        )


class TeamWithScoreOut(CustomBaseModel):
    id: uuid.UUID
    description: str
    flag: FlagOut
    score: Optional[NonNegativeInt] = None


class ScoreBetIn(CustomBaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    score: NonNegativeInt


class ScoreBetOut(CustomBaseModel):
    id: uuid.UUID
    locked: bool
    team1: Optional[TeamWithScoreOut] = None
    team2: Optional[TeamWithScoreOut] = None

    @classmethod
    def from_instance(
        cls,
        score_bet: "ScoreBetModel",
        *,
        locked: bool,
        lang: Lang,
    ) -> "ScoreBetOut":
        return cls(
            id=score_bet.id,
            locked=locked,
            team1=(
                TeamWithScoreOut(
                    id=score_bet.match.team1.id,
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
                    description=get_language_description(score_bet.match.team2, lang),
                    score=score_bet.score2,
                    flag=FlagOut(url=score_bet.match.team2.flag_url),
                )
                if score_bet.match.team2_id is not None
                else None
            ),
        )


class GroupOut(CustomBaseModel):
    id: uuid.UUID
    description: str

    score_bets: list[ScoreBetOut]
    binary_bets: list[BinaryBetOut]

    @classmethod
    def from_instance(cls, group: "GroupModel", *, lang: Lang) -> "GroupOut":
        return cls(
            id=group.id,
            description=get_language_description(group, lang),
            score_bets=[],
            binary_bets=[],
        )


class PhaseOut(CustomBaseModel):
    id: uuid.UUID
    description: str
    groups: list[GroupOut]

    @classmethod
    def from_instance(cls, phase: "PhaseModel", *, lang: Lang) -> "PhaseOut":
        return cls(id=phase.id, description=get_language_description(phase, lang), groups=[])


class RetrieveAllBetsOut(CustomBaseModel):
    phases: list[PhaseOut]


class LoginIn(CustomBaseModel):
    name: str
    password: str


class LoginOut(CustomBaseModel):
    id: uuid.UUID
    name: str
    token: str


class GenericOut(CustomBaseModel, Generic[Data]):
    data: Data
