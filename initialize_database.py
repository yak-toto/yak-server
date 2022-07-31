#!/usr/bin/env python3
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

        matches_index = {}

        for row in spamreader:
            group_name, team1_name, team2_name = row

            if group_name not in matches_index:
                matches_index[group_name] = 0

            team1 = Team.query.filter_by(description=team1_name).first()
            team2 = Team.query.filter_by(description=team2_name).first()

            phase = Phase.query.filter_by(code=group_name).first()

            db.session.add(
                Matches(
                    group_name=group_name,
                    phase_id=phase.id,
                    team1_id=team1.id,
                    team2_id=team2.id,
                    match_index=matches_index[group_name],
                )
            )

            matches_index[group_name] += 1

        db.session.commit()
