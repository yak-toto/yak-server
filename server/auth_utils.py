from functools import wraps

import jwt
from flask import current_app
from flask import request

from .models import User
from .utils import failed_response


def token_required(f):
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = request.headers.get("Authorization", "").split()

        invalid_msg = failed_response(
            401, "Invalid token. Registeration and / or authentication required"
        )
        expired_msg = failed_response(401, "Expired token. Reauthentication required.")

        if len(auth_headers) != 2:
            return invalid_msg

        try:
            token = auth_headers[1]
            data = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
            user = User.query.get(data["sub"])
            if not user:
                raise RuntimeError("User not found")
            return f(user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return expired_msg
        except (jwt.InvalidTokenError, Exception) as e:
            print(e)
            return invalid_msg

    return _verify
