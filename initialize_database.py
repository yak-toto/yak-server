#!/usr/bin/env python
import csv

from server import create_app
from server import db
from server.models import Group
from server.models import Match
from server.models import Phase
from server.models import Team

app = create_app()

with app.app_context():
    with open("data/phases.csv", newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter="|")

        db.session.add_all(Phase(code=row[0], description=row[1]) for row in spamreader)
        db.session.commit()

    with open("data/groups.csv", newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter="|")

        for row in spamreader:
            code, phase_code, description = row

            phase = Phase.query.filter_by(code=phase_code).first()

            db.session.add(Group(code=code, phase_id=phase.id, description=description))

        db.session.commit()

    with open("data/teams.csv", newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter="|")

        db.session.add_all(Team(code=row[0], description=row[1]) for row in spamreader)
        db.session.commit()

    with open("data/matches.csv", newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter="|")

        for row in spamreader:
            group_code, index, team1_code, team2_code = row

            team1 = Team.query.filter_by(code=team1_code).first()
            team2 = Team.query.filter_by(code=team2_code).first()

            group = Group.query.filter_by(code=group_code).first()

            db.session.add(
                Match(
                    group_id=group.id,
                    team1_id=team1.id,
                    team2_id=team2.id,
                    index=index,
                )
            )

        db.session.commit()
