from yak_server import db


class TableDropInProduction(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to drop database tables in production. DO NOT DO IT.")


def script(app):
    if not app.config.get("DEBUG"):
        raise TableDropInProduction

    with app.app_context():
        db.drop_all()
