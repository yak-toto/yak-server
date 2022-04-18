from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from . import db
from .models import Match

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

GROUPS = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name, groups=GROUPS)

@main.route('/group/<group_name>')
def group(group_name):
    if group_name not in GROUPS:
        return 'bad request!', 404

    matches = list(Match.query.filter_by(name=current_user.name, group_name=group_name))

    return render_template('group.html', group_name=group_name, groups=GROUPS, matches=matches)

@main.route('/group/<group_name>', methods=['POST'])
def group_post(group_name):
    if group_name not in GROUPS:
        return 'bad request!', 404

    score_first_column = request.form.getlist('score_first_column[]')
    score_second_column = request.form.getlist('score_second_column[]')

    matches = Match.query.filter_by(name=current_user.name, group_name=group_name)

    for index, match in enumerate(matches):
        match.score1 = score_first_column[index]
        match.score2 = score_second_column[index]

    (db.session.add(match) for match in matches)
    db.session.commit()

    return render_template('group.html', group_name=group_name, matches=matches)
