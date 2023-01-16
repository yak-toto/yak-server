#!/usr/bin/env python
import csv

from server import db
from server.database.models import GroupModel
from server.database.models import MatchModel
from server.database.models import PhaseModel
from server.database.models import TeamModel


def script(app):
    with app.app_context():
        COMPETITION = app.config["COMPETITION"]

        DATA_FOLDER = "tests" if app.config["TESTING"] else "data"

        with open(f"{DATA_FOLDER}/{COMPETITION}/phases.csv", newline="") as csvfile:
            spamreader = csv.reader(csvfile, delimiter="|")

            db.session.add_all(
                PhaseModel(code=row[0], description=row[1]) for row in spamreader
            )
            db.session.commit()

        with open(f"{DATA_FOLDER}/{COMPETITION}/groups.csv", newline="") as csvfile:
            spamreader = csv.reader(csvfile, delimiter="|")

            for row in spamreader:
                code, phase_code, description = row

                phase = PhaseModel.query.filter_by(code=phase_code).first()

                db.session.add(
                    GroupModel(code=code, phase_id=phase.id, description=description)
                )

            db.session.commit()

        with open(f"{DATA_FOLDER}/{COMPETITION}/teams.csv", newline="") as csvfile:
            spamreader = csv.reader(csvfile, delimiter="|")

            db.session.add_all(
                TeamModel(code=row[0], description=row[1]) for row in spamreader
            )
            db.session.commit()

        with open(f"{DATA_FOLDER}/{COMPETITION}/matches.csv", newline="") as csvfile:
            spamreader = csv.reader(csvfile, delimiter="|")

            for row in spamreader:
                group_code, index, team1_code, team2_code = row

                team1 = TeamModel.query.filter_by(code=team1_code).first()
                team2 = TeamModel.query.filter_by(code=team2_code).first()

                group = GroupModel.query.filter_by(code=group_code).first()

                db.session.add(
                    MatchModel(
                        group_id=group.id,
                        team1_id=team1.id,
                        team2_id=team2.id,
                        index=index,
                    )
                )

            db.session.commit()


if __name__ == "__main__":
    from server import create_app

    script(create_app())
