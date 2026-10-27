"""One-shot save confirmations, carried via a redirect query param.

No server-side session needed — same stateless spirit as `csrf.py`. The
message rides the redirect URL and is read back once by the template that
renders the next page; reloading that page loses it, which is the point.
"""
from __future__ import annotations

from urllib.parse import quote

from fastapi.responses import RedirectResponse


def redirect_with_message(url: str, message: str, status_code: int = 303) -> RedirectResponse:
    return RedirectResponse(url=f"{url}?flash={quote(message)}", status_code=status_code)
