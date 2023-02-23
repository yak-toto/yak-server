from flask import current_app
from flask.cli import AppGroup

from .database import (
    backup_database,
    create_admin,
    create_database,
    delete_database,
    drop_database,
    initialize_database,
)

db_cli = AppGroup("db")


@db_cli.command("create")
def create():
    create_database(current_app)


@db_cli.command("init")
def init():
    initialize_database(current_app)


@db_cli.command("drop")
def drop():
    drop_database(current_app)


@db_cli.command("delete")
def delete():
    delete_database(current_app)


@db_cli.command("admin")
def admin():
    create_admin(current_app)


@db_cli.command("backup")
def backup():
    backup_database(current_app)
