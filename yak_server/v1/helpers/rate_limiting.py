from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

auth_rate_limit = limiter.limit("5/minute")


def global_rate_limit(request: Request) -> None:
    """Enforce ``limiter``'s default limits for every request.

    slowapi's own ``SlowAPIMiddleware`` looks up the matching route by
    walking ``app.routes``, which no longer works since FastAPI wraps
    included routers in ``_IncludedRouter`` objects that aren't routes
    themselves. Calling the limiter directly, keyed off the request path,
    sidesteps that route lookup entirely.
    """
    limiter._check_request_limit(request, None, in_middleware=False)  # ruff:ignore[private-member-access]
