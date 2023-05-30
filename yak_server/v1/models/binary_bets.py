from typing import TYPE_CHECKING, Optional

from pydantic import UUID4, BaseModel, PositiveInt

from .groups import GroupIn, GroupOut
from .phases import PhaseOut
from .teams import FlagOut, TeamIn, TeamModifyBinaryBetIn, TeamWithWonOut

if TYPE_CHECKING:
    from yak_server.database.models import BinaryBetModel


class BinaryBetIn(BaseModel):
    is_one_won: Optional[bool]
    index: PositiveInt
    team1: TeamIn
    team2: TeamIn
    group: GroupIn


class BinaryBetOut(BaseModel):
    id: UUID4
    locked: bool
    team1: Optional[TeamWithWonOut]
    team2: Optional[TeamWithWonOut]

    @classmethod
    def from_instance(cls, binary_bet: "BinaryBetModel", locked: bool) -> "BinaryBetOut":
        return cls(
            id=binary_bet.id,
            locked=locked,
            team1=TeamWithWonOut(
                id=binary_bet.match.team1.id,
                code=binary_bet.match.team1.code,
                description=binary_bet.match.team1.description_fr,
                won=binary_bet.bet_from_is_one_won()[0],
                flag=FlagOut(url=binary_bet.match.team1.flag_url),
            )
            if binary_bet.match.team1
            else None,
            team2=TeamWithWonOut(
                id=binary_bet.match.team2.id,
                code=binary_bet.match.team2.code,
                description=binary_bet.match.team2.description_fr,
                won=binary_bet.bet_from_is_one_won()[1],
                flag=FlagOut(url=binary_bet.match.team2.flag_url),
            )
            if binary_bet.match.team2
            else None,
        )


class Group(BaseModel):
    id: UUID4


class BinaryBetWithGroupIdOut(BaseModel):
    id: UUID4
    locked: bool
    group: Group
    team1: Optional[TeamWithWonOut]
    team2: Optional[TeamWithWonOut]

    @classmethod
    def from_instance(cls, binary_bet: "BinaryBetModel", locked: bool) -> "BinaryBetWithGroupIdOut":
        return cls(
            id=binary_bet.id,
            locked=locked,
            group=Group(id=binary_bet.match.group_id),
            team1=TeamWithWonOut(
                id=binary_bet.match.team1.id,
                code=binary_bet.match.team1.code,
                description=binary_bet.match.team1.description_fr,
                won=binary_bet.bet_from_is_one_won()[0],
                flag=FlagOut(url=binary_bet.match.team1.flag_url),
            )
            if binary_bet.match.team1
            else None,
            team2=TeamWithWonOut(
                id=binary_bet.match.team2.id,
                code=binary_bet.match.team2.code,
                description=binary_bet.match.team2.description_fr,
                won=binary_bet.bet_from_is_one_won()[1],
                flag=FlagOut(url=binary_bet.match.team2.flag_url),
            )
            if binary_bet.match.team2
            else None,
        )


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
