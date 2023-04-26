from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jwt import decode as jwt_decode
from jwt import encode as jwt_encode


def encode_bearer_token(sub: str, expiration_time: timedelta, secret_key: str) -> str:
    return jwt_encode(
        {
            "sub": sub,
            "iat": datetime.now(tz=timezone.utc),
            "exp": datetime.now(tz=timezone.utc) + expiration_time,
        },
        secret_key,
        algorithm="HS512",
    )


def decode_bearer_token(token: str, secret_key: str) -> Dict[str, Any]:
    return jwt_decode(token, secret_key, algorithms=["HS512"])
