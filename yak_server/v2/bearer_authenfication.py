from functools import wraps

from flask import current_app
from jwt import ExpiredSignatureError, PyJWTError

from yak_server.database.models import UserModel
from yak_server.helpers.authentification import decode_bearer_token

from .result import ExpiredToken, InvalidToken, UnauthorizedAccessToAdminAPI
from .schema import User

NUMBER_ELEMENTS_IN_AUTHORIZATION = 2


def is_authentificated(f):  # noqa: ANN001, ANN201
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = kwargs["info"].context["request"].headers.get("Authorization", "").split()

        if len(auth_headers) != NUMBER_ELEMENTS_IN_AUTHORIZATION or auth_headers[0] != "Bearer":
            return InvalidToken()

        token = auth_headers[1]
        try:
            data = decode_bearer_token(token, current_app.config["SECRET_KEY"])
        except ExpiredSignatureError:
            return ExpiredToken()
        except PyJWTError:
            return InvalidToken()

        user = UserModel.query.filter_by(id=data["sub"]).first()
        if not user:
            return InvalidToken()

        kwargs["info"].user = User.from_instance(instance=user)

        return f(*args, **kwargs)

    return _verify


def is_admin_authentificated(f):  # noqa: ANN001, ANN201
    @wraps(f)
    def _verify(*args, **kwargs):
        if kwargs["info"].user.pseudo != "admin":
            return UnauthorizedAccessToAdminAPI()

        return f(*args, **kwargs)

    return _verify
