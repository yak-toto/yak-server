import json

from .models import Match


def initialize_matches(user_id):
    with open("server/matches.json") as f:
        matches = json.load(f)
        return (
            Match(
                user_id=user_id,
                group_name=group_name,
                team1=teams[0],
                score1=None,
                score2=None,
                team2=teams[1],
            )
            for group_name, group_matches in matches.items()
            for teams in group_matches
        )
