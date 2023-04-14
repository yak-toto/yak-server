from pydantic import BaseModel

from .generic import PositiveOrZeroInt
from .teams import TeamOut


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

    class Config:
        extra = "forbid"
        orm_mode = True
