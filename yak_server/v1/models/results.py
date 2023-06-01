from typing import TYPE_CHECKING

from pydantic import BaseModel, PositiveInt

from .generic import PositiveOrZeroInt

if TYPE_CHECKING:
    from yak_server.database.models import UserModel


class UserResult(BaseModel):
    rank: PositiveInt
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

    @classmethod
    def from_instance(cls, user: "UserModel", rank: PositiveInt) -> "UserResult":
        return cls(
            rank=rank,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            number_match_guess=user.number_match_guess,
            number_score_guess=user.number_score_guess,
            number_qualified_teams_guess=user.number_qualified_teams_guess,
            number_first_qualified_guess=user.number_first_qualified_guess,
            number_quarter_final_guess=user.number_quarter_final_guess,
            number_semi_final_guess=user.number_semi_final_guess,
            number_final_guess=user.number_final_guess,
            number_winner_guess=user.number_winner_guess,
            points=user.points,
        )
