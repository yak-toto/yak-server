from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Match
from . import db
from .telegram_sender import send_message
import json

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    password = request.form.get('password')
    name = request.form.get('name')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(name=name).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login')) # if the user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    send_message('User {} login.'.format(user.name))
    return redirect(url_for('main.profile'))

@auth.route('/signup')
def signup():
    # code to validate and add user to database goes here
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(name=name).first()

    if user: # if a user is found, we want to redirect back to signup page so user can try again
        flash('Name already exists')
        return redirect(url_for('auth.signup'))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(name=name, password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    send_message('New user created : username {}.\n'.format(new_user.name))

    # create matches table for user
    with open('project/matches.json', mode='r') as f:
        matches = json.load(f)
        for group_name, group_matches in matches.items():
            for teams in group_matches:
                db.session.add(Match(name=new_user.name, group_name=group_name, team1=teams[0], score1=None, score2=None, team2=teams[1]))
    db.session.commit()

    return render_template('signup.html')

@auth.route('/logout')
@login_required
def logout():
    send_message('User {} logout'.format(current_user.name))
    logout_user()
    return redirect(url_for('main.index'))