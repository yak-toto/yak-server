from functools import wraps

import jwt
from flask import current_app, request

from yak_server.database.models import UserModel

from .errors import UserNotFound

NUMBER_ELEMENTS_IN_AUTHORIZATION = 2


def token_required(f):
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = request.headers.get("Authorization", "").split()

        if auth_headers[0] != "Bearer" or len(auth_headers) != NUMBER_ELEMENTS_IN_AUTHORIZATION:
            raise jwt.InvalidTokenError

        token = auth_headers[1]
        data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])

        user = UserModel.query.filter_by(id=data["sub"]).first()
        if not user:
            raise UserNotFound

        return f(user, *args, **kwargs)

    return _verify
