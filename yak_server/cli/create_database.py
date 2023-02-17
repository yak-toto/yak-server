#!/usr/bin/env python
from yak_server import db


def script(app):
    with app.app_context():
        db.create_all()


if __name__ == "__main__":
    from yak_server import create_app

    script(create_app())
