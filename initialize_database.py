#!/usr/bin/env python
import csv

from server import create_app
from server import db
from server.models import Matches
from server.models import Phase
from server.models import Team

app = create_app()

with app.app_context():
    with open("data/teams.csv", newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter="|")

        db.session.add_all(Team(code=row[0], description=row[1]) for row in spamreader)
        db.session.commit()

    with open("data/phases.csv", newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter="|")

        db.session.add_all(
            Phase(code=row[0], phase_description=row[1], description=row[2])
            for row in spamreader
        )
        db.session.commit()

    with open("data/matches.csv", newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter="|")

        for row in spamreader:
            group_code, index, team1_code, team2_code = row

            team1 = Team.query.filter_by(code=team1_code).first()
            team2 = Team.query.filter_by(code=team2_code).first()

            phase = Phase.query.filter_by(code=group_code).first()

            db.session.add(
                Matches(
                    phase_id=phase.id,
                    team1_id=team1.id,
                    team2_id=team2.id,
                    index=index,
                )
            )

        db.session.commit()
