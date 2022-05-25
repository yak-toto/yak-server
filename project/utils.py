import json
from tokenize import group
from .models import Match


def initialize_matches(user_name):
    with open("project/matches.json", mode="r") as f:
        matches = json.load(f)
        return (
            Match(
                name=user_name,
                group_name=group_name,
                team1=teams[0],
                score1=None,
                score2=None,
                team2=teams[1],
            )
            for group_name, group_matches in matches.items()
            for teams in group_matches
        )
