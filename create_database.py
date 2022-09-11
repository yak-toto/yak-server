#!/usr/bin/env python
from server import db


def script(app):
    db.create_all(app=app)


if __name__ == "__main__":
    from server import create_app

    script(create_app())
