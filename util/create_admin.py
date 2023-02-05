#!/usr/bin/env python
from getpass import getpass

from yak_server import create_app, db
from yak_server.database.models import MatchModel, ScoreBetModel, UserModel


def script(app):
    with app.app_context():
        password = getpass(prompt="Admin user password: ")
        confirm_password = getpass(prompt="Confirm admin password: ")

        if password != confirm_password:
            print("ERROR : Password and Confirm Password fields does not match.")
            return

        user = UserModel(
            name="admin",
            first_name="admin",
            last_name="admin",
            password=password,
        )

        db.session.add(user)
        db.session.commit()

        db.session.add_all(
            ScoreBetModel(user_id=user.id, match_id=match.id) for match in MatchModel.query.all()
        )
        db.session.commit()


if __name__ == "__main__":
    app = create_app()
    script(app)
