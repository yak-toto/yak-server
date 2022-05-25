from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
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
    password = request.form.get("password")
    name = request.form.get("name")
    remember = True if request.form.get("remember") else False

    user = User.query.filter_by(name=name).first()

    if not user or not check_password_hash(user.password, password):
        flash("Please check your login details and try again.")
        return redirect(url_for("auth.login"))

    login_user(user, remember=remember)
    send_message(f"User {user.name} login.")
    return redirect(url_for("main.profile"))


@auth.route("/signup")
def signup():
    return render_template("signup.html")


@auth.route("/signup", methods=["POST"])
def signup_post():
    name = request.form.get("name")
    password = request.form.get("password")

    user = User.query.filter_by(name=name).first()

    if user:
        flash("Name already exists")
        return redirect(url_for("auth.signup"))

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

    return render_template("signup.html")


@auth.route("/logout")
@login_required
def logout():
    send_message(f"User {current_user.name} logout")
    logout_user()
    return redirect(url_for("main.index"))
