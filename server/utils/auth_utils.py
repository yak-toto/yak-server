from functools import wraps

import jwt
from flask import current_app
from flask import request

from ..models import User
from .errors import expired_token
from .errors import invalid_token
from .flask_utils import failed_response


def token_required(f):
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = request.headers.get("Authorization", "").split()

        invalid_msg = failed_response(*invalid_token)
        expired_msg = failed_response(*expired_token)

        if len(auth_headers) != 2:
            return invalid_msg

        try:
            token = auth_headers[1]
            data = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
            user = User.query.filter_by(id=data["sub"]).first()
            if not user:
                raise RuntimeError("User not found")
            return f(user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return expired_msg
        except (jwt.InvalidTokenError, Exception) as e:
            print(e)
            return invalid_msg

    return _verify
