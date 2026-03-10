from typing import NoReturn

from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter
from pyrate_limiter import Duration, Limiter, Rate, RedisBucket  # type: ignore[attr-defined]
from redis import Redis

from yak_server.database.settings import RedisSettings

from .errors import RateLimitExceeded


def rate_limiting_callback(_: Request, __: Response) -> NoReturn:
    raise RateLimitExceeded


def instantiate_rate_limiter(namespace: str, rates: list[Rate], scope: str) -> RateLimiter:
    settings = RedisSettings()

    redis_db = Redis(host=settings.host, password=settings.password, port=settings.port)

    bucket_key = f"rate_limit:{scope}"

    if namespace:
        bucket_key = f"{namespace}:{bucket_key}"

    bucket = RedisBucket.init(rates, redis_db, bucket_key)

    return RateLimiter(Limiter(bucket), callback=rate_limiting_callback)


def instantiate_global_rate_limiter(namespace: str = "") -> RateLimiter:
    return instantiate_rate_limiter(
        namespace=namespace, rates=[Rate(200, Duration.MINUTE)], scope="global"
    )


def instantiate_signup_rate_limiter(namespace: str = "") -> RateLimiter:
    return instantiate_rate_limiter(
        namespace=namespace, rates=[Rate(5, Duration.MINUTE)], scope="signup"
    )


def instantiate_login_rate_limiter(namespace: str = "") -> RateLimiter:
    return instantiate_rate_limiter(
        namespace=namespace, rates=[Rate(5, Duration.MINUTE)], scope="login"
    )
