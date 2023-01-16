from getpass import getpass

from server import create_app
from server import db
from server.models import UserModel


def script(app):
    with app.app_context():
        db.session.add(
            UserModel(
                name="admin",
                first_name="admin",
                last_name="admin",
                password=getpass(prompt="Admin user password: "),
            )
        )
        db.session.commit()


if __name__ == "__main__":
    app = create_app()
    script(app)
