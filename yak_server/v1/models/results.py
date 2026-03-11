from typing import TYPE_CHECKING

from pydantic import UUID4, BaseModel, NonNegativeInt

from yak_server.helpers.language import Lang

from .groups import GroupOut

if TYPE_CHECKING:
    from yak_server.database.models import UserKnockoutGuessModel, UserModel


class KnockoutRoundResult(BaseModel):
    group: GroupOut
    count: NonNegativeInt

    @classmethod
    def from_instance(
        cls, user_knockout_guess: "UserKnockoutGuessModel", *, lang: Lang
    ) -> "KnockoutRoundResult":
        return cls(
            group=GroupOut.from_instance(user_knockout_guess.group, lang=lang),
            count=user_knockout_guess.count,
        )


class KnockoutRoundCount(BaseModel):
    group_id: UUID4
    count: NonNegativeInt


class UserResult(BaseModel):
    rank: NonNegativeInt
    first_name: str
    last_name: str
    full_name: str
    number_match_guess: NonNegativeInt
    number_score_guess: NonNegativeInt
    number_qualified_teams_guess: NonNegativeInt
    number_first_qualified_guess: NonNegativeInt
    knockout_rounds: list[KnockoutRoundResult]
    number_winner_guess: NonNegativeInt
    points: float

    @classmethod
    def from_instance(cls, user: "UserModel", *, rank: NonNegativeInt, lang: Lang) -> "UserResult":
        return cls(
            rank=rank,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            number_match_guess=user.number_match_guess,
            number_score_guess=user.number_score_guess,
            number_qualified_teams_guess=user.number_qualified_teams_guess,
            number_first_qualified_guess=user.number_first_qualified_guess,
            knockout_rounds=[
                KnockoutRoundResult.from_instance(kg, lang=lang)
                for kg in sorted(user.knockout_guesses, key=lambda kg: kg.group.index)
            ],
            number_winner_guess=user.number_winner_guess,
            points=user.points,
        )


class ScoreBoardUserResult(BaseModel):
    rank: NonNegativeInt
    first_name: str
    last_name: str
    full_name: str
    number_match_guess: NonNegativeInt
    number_score_guess: NonNegativeInt
    number_qualified_teams_guess: NonNegativeInt
    number_first_qualified_guess: NonNegativeInt
    knockout_rounds: list[KnockoutRoundCount]
    number_winner_guess: NonNegativeInt
    points: float

    @classmethod
    def from_instance(cls, user: "UserModel", *, rank: NonNegativeInt) -> "ScoreBoardUserResult":
        return cls(
            rank=rank,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            number_match_guess=user.number_match_guess,
            number_score_guess=user.number_score_guess,
            number_qualified_teams_guess=user.number_qualified_teams_guess,
            number_first_qualified_guess=user.number_first_qualified_guess,
            knockout_rounds=[
                KnockoutRoundCount(group_id=kg.group_id, count=kg.count)
                for kg in sorted(user.knockout_guesses, key=lambda kg: kg.group.index)
            ],
            number_winner_guess=user.number_winner_guess,
            points=user.points,
        )


class ScoreBoardResponse(BaseModel):
    groups: list[GroupOut]
    results: list[ScoreBoardUserResult]
