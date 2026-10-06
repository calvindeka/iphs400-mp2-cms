"""Double-submit-cookie CSRF protection for state-changing forms.

A random token is set as a plain (non-httponly) cookie; every form that
mutates state embeds the same value as a hidden field. A cross-site POST
can't read the victim's cookie to put a matching value in its own forged
form, so a mismatch means the request didn't originate from a page we
rendered. Stateless — no server-side session needed.

Login itself is the one state-changing form that's exempt: it establishes
the session rather than acting on an existing one, there's nothing yet to
forge an action against, and `tests/conftest.py`'s given `client_as` fixture
logs in with a bare POST, confirming the template's own design doesn't
expect a token there. Logout and every later ticket's forms (posts, pages,
users) use this module.
"""
from __future__ import annotations

import secrets

from fastapi import Form, HTTPException, Request, Response

COOKIE_NAME = "csrf_token"


def get_or_create_token(request: Request) -> str:
    """The request's current CSRF token, or a fresh one if it has none yet.

    Split from `apply_cookie` because a template needs the token value
    *before* the response it will be set on exists.
    """
    return request.cookies.get(COOKIE_NAME) or secrets.token_urlsafe(32)


def apply_cookie(request: Request, response: Response, token: str) -> None:
    """Set the cookie on `response` if `request` didn't already have it."""
    if request.cookies.get(COOKIE_NAME) != token:
        response.set_cookie(COOKIE_NAME, token, samesite="lax")


def validate(request: Request, submitted_token: str) -> bool:
    cookie_token = request.cookies.get(COOKIE_NAME)
    return bool(cookie_token) and secrets.compare_digest(cookie_token, submitted_token)


def require_valid(request: Request, csrf_token: str = Form(...)) -> None:
    """A route dependency: `Depends(csrf.require_valid)` 400s a forged/missing
    token, so every state-changing route gets the same one-line guard."""
    if not validate(request, csrf_token):
        raise HTTPException(status_code=400, detail="Invalid or missing CSRF token")
