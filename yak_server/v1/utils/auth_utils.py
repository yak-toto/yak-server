from functools import wraps

from flask import current_app, request
from jwt import InvalidTokenError

from yak_server.database.models import UserModel
from yak_server.helpers.authentification import decode_bearer_token

from .errors import UserNotFound

NUMBER_ELEMENTS_IN_AUTHORIZATION = 2


def token_required(f):
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = request.headers.get("Authorization", "").split()

        if len(auth_headers) != NUMBER_ELEMENTS_IN_AUTHORIZATION or auth_headers[0] != "Bearer":
            raise InvalidTokenError

        token = auth_headers[1]
        data = decode_bearer_token(token, current_app.config["SECRET_KEY"])

        user = UserModel.query.filter_by(id=data["sub"]).first()
        if not user:
            raise UserNotFound

        return f(user, *args, **kwargs)

    return _verify
