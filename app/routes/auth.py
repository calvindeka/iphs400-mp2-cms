"""Login and logout for the admin console."""
from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app import auth, csrf, db, settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES))

GENERIC_LOGIN_ERROR = "Incorrect email or password."


@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(request, "admin/login.html", {"title": "Log in", "error": None})


@router.post("/login")
def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if row is None or not row["active"] or not auth.verify_password(password, row["password_hash"]):
        return templates.TemplateResponse(
            request, "admin/login.html",
            {"title": "Log in", "error": GENERIC_LOGIN_ERROR}, status_code=400,
        )

    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie(
        auth.SESSION_COOKIE, auth.session_cookie_value(row["id"]),
        httponly=True, samesite="lax",
    )
    return response


@router.post("/logout")
def logout(request: Request, csrf_token: str = Form(...)):
    if not csrf.validate(request, csrf_token):
        raise HTTPException(status_code=400, detail="Invalid or missing CSRF token")
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(auth.SESSION_COOKIE)
    return response
