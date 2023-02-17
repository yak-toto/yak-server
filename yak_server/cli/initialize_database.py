#!/usr/bin/env python
import csv
from pathlib import Path

from yak_server import db
from yak_server.database.models import GroupModel, MatchModel, PhaseModel, TeamModel


def script(app):
    with app.app_context():
        DATA_FOLDER = app.config["DATA_FOLDER"]

        with Path(f"{DATA_FOLDER}/phases.csv", newline="").open() as csvfile:
            spamreader = csv.reader(csvfile, delimiter="|")

            for row in spamreader:
                index, code, description = row
                db.session.add(PhaseModel(code=code, description=description, index=index))

            db.session.commit()

        with Path(f"{DATA_FOLDER}/groups.csv", newline="").open() as csvfile:
            spamreader = csv.reader(csvfile, delimiter="|")

            for row in spamreader:
                index, code, phase_code, description = row

                phase = PhaseModel.query.filter_by(code=phase_code).first()

                db.session.add(
                    GroupModel(code=code, phase_id=phase.id, description=description, index=index),
                )

            db.session.commit()

        with Path(f"{DATA_FOLDER}/teams.csv", newline="").open() as csvfile:
            spamreader = csv.reader(csvfile, delimiter="|")

            db.session.add_all(TeamModel(code=row[0], description=row[1]) for row in spamreader)
            db.session.commit()

        with Path(f"{DATA_FOLDER}/matches.csv", newline="").open() as csvfile:
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
                    ),
                )

            db.session.commit()


if __name__ == "__main__":
    from yak_server import create_app

    script(create_app())
