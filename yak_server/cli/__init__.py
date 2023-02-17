from flask import current_app
from flask.cli import AppGroup

from .backup_database import script as backup_database
from .create_admin import script as create_admin
from .create_database import script as create_database
from .delete_database import script as delete_database
from .initialize_database import script as initialize_database

db_cli = AppGroup("db")


@db_cli.command("create")
def create():
    create_database(current_app)


@db_cli.command("init")
def init():
    initialize_database(current_app)


@db_cli.command("delete")
def delete():
    delete_database(current_app)


@db_cli.command("admin")
def admin():
    create_admin(current_app)


@db_cli.command("backup")
def backup():
    backup_database(current_app)
