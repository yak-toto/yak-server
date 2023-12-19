import warnings
from dataclasses import dataclass
from typing import List, Optional, Tuple

import httpx
from sqlalchemy import and_

from yak_server.database import SessionLocal
from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    MatchModel,
    ScoreBetModel,
    TeamModel,
    UserModel,
)
from yak_server.helpers.settings import get_settings

try:
    import bs4
except ImportError:  # pragma: no cover
    bs4 = None  # type: ignore[assignment]

try:
    import lxml
except ImportError:  # pragma: no cover
    lxml = None  # type: ignore[assignment]


def parse_score(content: str) -> Tuple[int, int]:
    try:
        scores = next(next(content.children).children)
    except AttributeError:
        return None, None

    try:
        score1_str, score2_str = scores.split("\u2013")
    except ValueError:  # pragma: no cover
        return None, None

    try:
        score1 = int(score1_str)
    except ValueError:  # pragma: no cover
        warnings.warn(f"Couldn't parse score1: '{score1_str}'", stacklevel=2)
        score1 = None

    try:
        score2 = int(score2_str)
    except ValueError:  # pragma: no cover
        warnings.warn(f"Couldn't parse score2: '{score2_str}'", stacklevel=2)
        score2 = None

    return score1, score2


def parse_penalty(content: str) -> bool:
    penalties_tag = content.find("a", string="Penalties")
    score_content = penalties_tag.next.parent.find_next("th").string

    score1, score2 = score_content.split("\u2013")

    return int(score1) > int(score2)


def is_penalties(content: str) -> bool:
    return bool(content.find("a", string="Penalties"))


class SyncOfficialResultsNotAvailableError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "Synchronize official results is not available without beautifulsoup4 installed. "
            "To enable it, please run: pip install beautifulsoup4[lxml]"
        )


@dataclass
class GroupContainer:
    model: GroupModel
    content: str


@dataclass
class Group:
    index: int


@dataclass
class Team:
    score: int
    description: str
    won: Optional[bool] = None


@dataclass
class Match:
    index: int
    group: Group
    team1: Team
    team2: Team


def extract_matches_from_html(groups: List[GroupContainer]) -> List[Match]:
    matches = []

    for index, group in enumerate(groups, start=1):
        try:
            next_group = groups[index + 1]
        except IndexError:
            next_group = None

        previous_matches_html = (
            frozenset(next_group.content.find_all_previous("div", class_="footballbox"))
            if next_group is not None
            else None
        )

        next_matches_html = group.content.find_all_next("div", class_="footballbox")

        matches_html = [
            match
            for match in next_matches_html
            if previous_matches_html is None or match in previous_matches_html
        ]

        for match_index, match_html in enumerate(matches_html, start=1):
            score1, score2 = parse_score(match_html.find("th", class_="fscore"))

            match = Match(
                index=match_index,
                group=Group(index=group.model.index),
                team1=Team(
                    description=(
                        match_html.find("th", class_="fhome").get_text().replace("\xa0", "")
                    ),
                    score=score1,
                ),
                team2=Team(
                    description=(
                        match_html.find("th", class_="faway").get_text().replace("\xa0", "")
                    ),
                    score=score2,
                ),
            )

            if is_penalties(match_html):
                is_one_won = parse_penalty(match_html)

                match.team1.won = is_one_won
                match.team2.won = not is_one_won

            matches.append(match)

    return matches


def synchronize_official_results() -> None:
    if bs4 is None or lxml is None:
        raise SyncOfficialResultsNotAvailableError

    official_results_url = get_settings().official_results_url

    response = httpx.get(str(official_results_url))

    soup = bs4.BeautifulSoup(response.text, "lxml")

    db = SessionLocal()

    groups = [
        GroupContainer(model=group, content=content.parent.parent)
        for group in db.query(GroupModel).order_by(GroupModel.index)
        for content in soup.find("span", string=group.description_en, class_="mw-headline")
    ]

    matches = extract_matches_from_html(groups)

    admin = db.query(UserModel).filter_by(name="admin").first()

    for match in matches:
        score_bet = (
            admin.score_bets.join(ScoreBetModel.match)
            .join(MatchModel.group)
            .filter(and_(GroupModel.index == match.group.index, MatchModel.index == match.index))
            .first()
        )

        if score_bet is not None:
            score_bet.score1 = match.team1.score
            score_bet.score2 = match.team2.score

        binary_bet = (
            admin.binary_bets.join(BinaryBetModel.match)
            .join(MatchModel.group)
            .join(GroupModel.phase)
            .filter(and_(GroupModel.index == match.group.index, MatchModel.index == match.index))
            .first()
        )

        if binary_bet is not None:
            team1 = db.query(TeamModel).filter_by(description_en=match.team1.description).first()
            team2 = db.query(TeamModel).filter_by(description_en=match.team2.description).first()

            if team1 is not None and team2 is not None:
                binary_bet.match.team1_id = team1.id
                binary_bet.match.team2_id = team2.id

                if match.team1.won is not None:
                    binary_bet.is_one_won = match.team1.won
                else:
                    binary_bet.is_one_won = match.team1.score > match.team2.score

    db.commit()
