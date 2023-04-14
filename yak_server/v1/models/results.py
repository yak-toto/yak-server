from pydantic import BaseModel, PositiveInt

from .generic import PositiveOrZeroInt


class UserResult(BaseModel):
    rank: PositiveInt = 1
    first_name: str
    last_name: str
    full_name: str
    number_match_guess: PositiveOrZeroInt
    number_score_guess: PositiveOrZeroInt
    number_qualified_teams_guess: PositiveOrZeroInt
    number_first_qualified_guess: PositiveOrZeroInt
    number_quarter_final_guess: PositiveOrZeroInt
    number_semi_final_guess: PositiveOrZeroInt
    number_final_guess: PositiveOrZeroInt
    number_winner_guess: PositiveOrZeroInt
    points: float

    class Config:
        orm_mode = True
