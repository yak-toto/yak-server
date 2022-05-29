from flask import Blueprint
from flask import render_template
from flask import request
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from . import db
from .models import User
from .telegram_sender import send_message
from .utils import initialize_matches

auth = Blueprint("auth", __name__)


@auth.route("/login")
def login():
    return render_template("login.html")


@auth.route("/login", methods=["POST"])
def login_post():
    body = request.get_json()

    name = body["name"]
    password = body["password"]
    remember = body.get("remember", False)

    user = User.query.filter_by(name=name).first()

    if not user or not check_password_hash(user.password, password):
        return "Login not found", 404

    login_user(user, remember=remember)
    send_message(f"User {user.name} login.")

    return "Login successful", 200


@auth.route("/signup")
def signup():
    return render_template("signup.html")


@auth.route("/signup", methods=["POST"])
def signup_post():
    body = request.get_json()
    name = body["name"]
    password = body["password"]

    user = User.query.filter_by(name=name).first()

    if user:
        return "Name already exists", 409

    new_user = User(
        name=name, password=generate_password_hash(password, method="sha256")
    )

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    send_message(f"New user created : username {new_user.name}.")

    for match in initialize_matches(new_user.name):
        db.session.add(match)
    db.session.commit()

    return "Signup successful", 201


@auth.route("/logout")
@login_required
def logout():
    send_message(f"User {current_user.name} logout")
    logout_user()
    return "Logout successful", 200
