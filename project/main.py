from flask import Blueprint, render_template
from flask_login import login_required, current_user
from . import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)

# @app.route('/')
# def index():
#     id = request.args.get("id", default=0, type=int)
#     name = request.args.get("name", default="", type=str)

#     return f"get: {id}, {name}\n"

# @app.route('/', methods=['POST'])
# def post():
#     return "post\n"

# @app.route('/scores/<user>', methods=['POST'])
# def post_scores(user):
#     with open('matches.json', 'r') as f:
#         matches = json.load(f)

#     if path.exists(f'results/{user}.json'):
#         print('ressource already exists')
#         abort(400)

#     print(matches)

#     with open(f'results/{user}.json', 'w') as f:
#         d = {key: [{ v[0]: 0, v[1]: 0 } for v in value] for key, value in matches.items()}

#         json_object = json.dumps(d, indent = 4) 

#         f.write(json_object)                

#     return f"{user}\n"

# @app.route('/scores/<user>', methods=['GET'])
# def get_scores(user):
#     if not path.exists(f'results/{user}.json'):
#         abort(400)

#     with open(f'results/{user}.json', 'r') as f:
#         results = json.load(f)

#     return f"{results}\n"

# @app.route('/scores/<user>', methods=['PATCH'])
# def patch_scores(user):
#     return f"{user}\n"

# @app.route('/real_results', methods=['POST'])
# def post_real_results():
#     group = request.args.get('group', type=str)
#     with open('matches.json', 'r') as f:
#         matches = json.load(f)
#         list_group = list(matches)

#     if group not in list_group:
#         abort(400)

#     team_1 = request.args.get('team_1', type=str)
#     team_2 = request.args.get('team_2', type=str)

#     print(matches[group])
#     print([team_1, team_2])

#     if [team_1, team_2] not in matches[group]:
#         abort(400)
    
#     score_1 = request.args.get('score_1', default=0, type=int)
#     score_2 = request.args.get('score_2', default=0, type=int)

#     with open('real_results.json', 'r') as f:
#         real_results = json.load(f)

#     with open('real_results.json', 'w') as f:
#         if group not in real_results:
#             real_results[group] = [] 

#         real_results[group].append( { team_1: score_1, team_2: score_2 })
#         f.write(json.dumps(real_results))

#     return "OK\n"

# @app.route('/user', methods=['POST'])
# def post_user():
#     conn = database.create_connection('user/users.db')
#     body = request.get_json()
#     with conn:
#         crypted_password = hashlib.md5(body["password"])
#         database.create_user(conn, body["username"], crypted_password)
#     return "OK"

# @app.route('/user/login', methods=['GET'])
# def login():
#     pass

# @app.route('/user/logout', methods=['GET'])
# def logout():
#     pass

# @app.route('/user/<username>', methods=['GET'])
# def get_user(username):
#     return 'OK'
