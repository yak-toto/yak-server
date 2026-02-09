from fastapi import Response

from .settings import CookieSettings

ACCESS_TOKEN_COOKIE = "access_token"  # noqa: S105 - This is not a secret, just the name of the cookie.
REFRESH_TOKEN_COOKIE = "refresh_token"  # noqa: S105 - This is not a secret, just the name of the cookie.


def set_auth_cookies(
    response: Response,
    access_token: str,
    access_expires_in: int,
    refresh_token: str,
    refresh_expires_in: int,
    settings: CookieSettings,
) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        max_age=access_expires_in,
        path="/api",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain or None,
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        max_age=refresh_expires_in,
        path="/api/v1/users/refresh",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain or None,
    )


def clear_auth_cookies(response: Response, settings: CookieSettings) -> None:
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        path="/api",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain or None,
    )
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        path="/api/v1/users/refresh",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain or None,
    )
