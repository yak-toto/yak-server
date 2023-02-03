#!/usr/bin/env python
from getpass import getpass

from server import create_app
from server import db
from server.database.models import MatchModel
from server.database.models import ScoreBetModel
from server.database.models import UserModel


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
            ScoreBetModel(user_id=user.id, match_id=match.id)
            for match in MatchModel.query.all()
        )
        db.session.commit()


if __name__ == "__main__":
    app = create_app()
    script(app)
