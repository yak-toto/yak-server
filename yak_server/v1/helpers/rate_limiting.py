from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter
from pyrate_limiter import Duration, Limiter, Rate

from yak_server.v1.helpers.errors import RateLimitExceeded


def rate_limiting_callback(_: Request, __: Response) -> None:
    raise RateLimitExceeded


def instantiate_global_rate_limiter() -> RateLimiter:
    return RateLimiter(Limiter(Rate(200, Duration.MINUTE)), callback=rate_limiting_callback)


def instantiate_auth_rate_limiter() -> RateLimiter:
    return RateLimiter(Limiter(Rate(5, Duration.MINUTE)), callback=rate_limiting_callback)
