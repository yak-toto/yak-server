from datetime import datetime, timedelta

from jwt import encode as jwt_encode


def encode_bearer_token(sub: str, expiration_time: timedelta, secret_key: str) -> str:
    return jwt_encode(
        {
            "sub": sub,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + expiration_time,
        },
        secret_key,
    )
