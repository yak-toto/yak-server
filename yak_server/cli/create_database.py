from yak_server import db


def script(app):
    with app.app_context():
        db.create_all()
