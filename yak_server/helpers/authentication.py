from typing import Any, Dict
from uuid import UUID

import pendulum
from jwt import decode as jwt_decode
from jwt import encode as jwt_encode


def encode_bearer_token(
    sub: UUID,
    expiration_time: pendulum.Duration,
    secret_key: str,
) -> str:
    return jwt_encode(
        {
            "sub": str(sub),
            "iat": pendulum.now("UTC"),
            "exp": pendulum.now("UTC") + expiration_time,
        },
        secret_key,
        algorithm="HS512",
    )


def decode_bearer_token(token: str, secret_key: str) -> Dict[str, Any]:
    return jwt_decode(token, secret_key, algorithms=["HS512"])
