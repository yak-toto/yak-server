from typing import TYPE_CHECKING

from pydantic import UUID4, BaseModel, ConfigDict, PositiveInt

from yak_server.helpers.language import Lang, get_language_description

from .groups import GroupIdOut, GroupIn, GroupOut
from .phases import PhaseOut
from .teams import FlagOut, TeamIn, TeamModifyBinaryBetIn, TeamWithWonOut

if TYPE_CHECKING:
    from yak_server.database.models import BinaryBetModel


class BinaryBetIn(BaseModel):
    is_one_won: bool | None = None
    index: PositiveInt
    team1: TeamIn
    team2: TeamIn
    group: GroupIn


class BinaryBetOut(BaseModel):
    id: UUID4
    locked: bool
    team1: TeamWithWonOut | None = None
    team2: TeamWithWonOut | None = None

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
                    code=binary_bet.match.team1.code,
                    description=get_language_description(binary_bet.match.team1, lang),
                    won=binary_bet.bet_from_is_one_won()[0],
                    flag=FlagOut(url=f"/api/v1/teams/{binary_bet.match.team1.id}/flag"),
                )
                if binary_bet.match.team1
                else None
            ),
            team2=(
                TeamWithWonOut(
                    id=binary_bet.match.team2.id,
                    code=binary_bet.match.team2.code,
                    description=get_language_description(binary_bet.match.team2, lang),
                    won=binary_bet.bet_from_is_one_won()[1],
                    flag=FlagOut(url=f"/api/v1/teams/{binary_bet.match.team2.id}/flag"),
                )
                if binary_bet.match.team2
                else None
            ),
        )


class BinaryBetWithGroupIdOut(BaseModel):
    id: UUID4
    locked: bool
    group: GroupIdOut
    team1: TeamWithWonOut | None = None
    team2: TeamWithWonOut | None = None

    @classmethod
    def from_instance(
        cls,
        binary_bet: "BinaryBetModel",
        *,
        locked: bool,
        lang: Lang,
    ) -> "BinaryBetWithGroupIdOut":
        return cls(
            id=binary_bet.id,
            locked=locked,
            group=GroupIdOut(id=binary_bet.match.group_id),
            team1=(
                TeamWithWonOut(
                    id=binary_bet.match.team1.id,
                    code=binary_bet.match.team1.code,
                    description=get_language_description(binary_bet.match.team1, lang),
                    won=binary_bet.bet_from_is_one_won()[0],
                    flag=FlagOut(url=f"/api/v1/teams/{binary_bet.match.team1.id}/flag"),
                )
                if binary_bet.match.team1
                else None
            ),
            team2=(
                TeamWithWonOut(
                    id=binary_bet.match.team2.id,
                    code=binary_bet.match.team2.code,
                    description=get_language_description(binary_bet.match.team2, lang),
                    won=binary_bet.bet_from_is_one_won()[1],
                    flag=FlagOut(url=f"/api/v1/teams/{binary_bet.match.team2.id}/flag"),
                )
                if binary_bet.match.team2
                else None
            ),
        )


class BinaryBetResponse(BaseModel):
    phase: PhaseOut
    group: GroupOut
    binary_bet: BinaryBetOut

    @classmethod
    def from_instance(
        cls,
        binary_bet: "BinaryBetModel",
        *,
        locked: bool,
        lang: Lang,
    ) -> "BinaryBetResponse":
        return cls(
            phase=PhaseOut.from_instance(binary_bet.match.group.phase, lang=lang),
            group=GroupOut.from_instance(binary_bet.match.group, lang=lang),
            binary_bet=BinaryBetOut.from_instance(binary_bet, locked=locked, lang=lang),
        )


class ModifyBinaryBetIn(BaseModel):
    is_one_won: bool | None = None
    team1: TeamModifyBinaryBetIn | None = None
    team2: TeamModifyBinaryBetIn | None = None

    model_config = ConfigDict(extra="forbid")
