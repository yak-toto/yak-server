import json

from server import create_app
from server import db
from server.models import Matches

app = create_app()

with app.app_context():
    with open("data/matches.json") as file:
        matches = json.loads(file.read())

        matches_index = {}

        for match in matches:
            if match["group_name"] not in matches_index:
                matches_index[match["group_name"]] = 0

            db.session.add(
                Matches(
                    group_name=match["group_name"],
                    team1=match["teams"][0],
                    team2=match["teams"][1],
                    match_index=matches_index[match["group_name"]],
                )
            )

            matches_index[match["group_name"]] += 1

        db.session.commit()
