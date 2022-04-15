from flask import Blueprint, render_template
from flask_login import login_required, current_user
from . import db
from .models import Match

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)

GROUPS = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')

@main.route('/group/<group_name>')
def group(group_name):
    if group_name not in GROUPS:
        return 'bad request!', 404

    matches = Match.query.filter_by(name=current_user.name, group_name=group_name)

    return render_template('profile.html', name=current_user.name)
