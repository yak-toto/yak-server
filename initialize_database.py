import csv

from server import create_app
from server import db
from server.models import Matches

app = create_app()

with app.app_context():
    with open("data/matches.csv", newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter="|")

        matches_index = {}

        for row in spamreader:
            group_name, team1, team2 = row

            if group_name not in matches_index:
                matches_index[group_name] = 0

            db.session.add(
                Matches(
                    group_name=group_name,
                    team1=team1,
                    team2=team2,
                    match_index=matches_index[group_name],
                )
            )

            matches_index[group_name] += 1

        db.session.commit()
