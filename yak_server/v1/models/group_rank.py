from typing import TYPE_CHECKING

from pydantic import BaseModel, NonNegativeInt

from .teams import TeamOut

if TYPE_CHECKING:
    from yak_server.database.models import GroupPositionModel
    from yak_server.helpers.language import Lang


class GroupPositionOut(BaseModel):
    team: TeamOut
    played: NonNegativeInt
    won: NonNegativeInt
    drawn: NonNegativeInt
    lost: NonNegativeInt
    goals_for: NonNegativeInt
    goals_against: NonNegativeInt
    goals_difference: int
    points: NonNegativeInt

    @classmethod
    def from_instance(
        cls,
        group_position: "GroupPositionModel",
        *,
        lang: "Lang",
    ) -> "GroupPositionOut":
        return cls(
            team=TeamOut.from_instance(group_position.team, lang=lang),
            played=group_position.played,
            won=group_position.won,
            drawn=group_position.drawn,
            lost=group_position.lost,
            goals_for=group_position.goals_for,
            goals_against=group_position.goals_against,
            goals_difference=group_position.goals_difference,
            points=group_position.points,
        )
