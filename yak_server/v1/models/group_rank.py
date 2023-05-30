from typing import TYPE_CHECKING

from pydantic import BaseModel

from .generic import PositiveOrZeroInt
from .teams import TeamOut

if TYPE_CHECKING:
    from yak_server.database.models import GroupPositionModel


class GroupPositionOut(BaseModel):
    team: TeamOut
    played: PositiveOrZeroInt
    won: PositiveOrZeroInt
    drawn: PositiveOrZeroInt
    lost: PositiveOrZeroInt
    goals_for: PositiveOrZeroInt
    goals_against: PositiveOrZeroInt
    goals_difference: int
    points: PositiveOrZeroInt

    @classmethod
    def from_instance(cls, group_position: "GroupPositionModel") -> "GroupPositionOut":
        return cls(
            team=TeamOut.from_instance(group_position.team),
            played=group_position.played,
            won=group_position.won,
            drawn=group_position.drawn,
            lost=group_position.lost,
            goals_for=group_position.goals_for,
            goals_against=group_position.goals_against,
            goals_difference=group_position.goals_difference,
            points=group_position.points,
        )
