"""Admin-only user management: create, change role, deactivate.

The last-admin guard applies to both role changes and deactivation — demoting
Tom to editor is exactly as dangerous as deactivating him when he's the only
admin left (CONTEXT.md: "Last-admin lockout").
"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app import auth, csrf, db, settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES))

ROLES = {"admin", "editor"}
LAST_ADMIN_ERROR = "Can't remove the last admin — promote someone else first."
DUPLICATE_EMAIL_ERROR = "A user with that email already exists."
INVALID_ROLE_ERROR = "Role must be admin or editor."


def _render(request: Request, user: auth.User, error: str | None = None, status_code: int = 200):
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY email").fetchall()
    token = csrf.get_or_create_token(request)
    response = templates.TemplateResponse(
        request, "admin/users.html",
        {"title": auth.console_label(user), "user": user, "users": rows,
         "csrf_token": token, "error": error},
        status_code=status_code,
    )
    csrf.apply_cookie(request, response, token)
    return response


def _would_drop_last_admin(conn: sqlite3.Connection, target: sqlite3.Row, removing: bool) -> bool:
    """True if `target` is an active admin and removing them (demoting or
    deactivating) would leave zero active admins."""
    if target["role"] != "admin" or not target["active"] or not removing:
        return False
    return auth.count_active_admins(conn) <= 1


@router.get("/admin/users")
def list_users(request: Request, user: auth.User = Depends(auth.require_role("admin"))):
    return _render(request, user)


@router.post("/admin/users")
def create_user(request: Request, email: str = Form(...), password: str = Form(...),
                 role: str = Form(...),
                 user: auth.User = Depends(auth.require_role("admin")),
                 _csrf: None = Depends(csrf.require_valid)):
    if role not in ROLES:
        return _render(request, user, error=INVALID_ROLE_ERROR, status_code=400)
    with db.connect() as conn:
        try:
            conn.execute(
                "INSERT INTO users (email, password_hash, role, active) VALUES (?, ?, ?, 1)",
                (email, auth.hash_password(password), role),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return _render(request, user, error=DUPLICATE_EMAIL_ERROR, status_code=400)
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/admin/users/{user_id}/role")
def change_role(request: Request, user_id: int, role: str = Form(...),
                 user: auth.User = Depends(auth.require_role("admin")),
                 _csrf: None = Depends(csrf.require_valid)):
    if role not in ROLES:
        return _render(request, user, error=INVALID_ROLE_ERROR, status_code=400)
    with db.connect() as conn:
        target = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if target is None:
            raise HTTPException(status_code=404)
        if _would_drop_last_admin(conn, target, removing=role != "admin"):
            return _render(request, user, error=LAST_ADMIN_ERROR, status_code=400)
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        conn.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/admin/users/{user_id}/deactivate")
def deactivate_user(request: Request, user_id: int,
                     user: auth.User = Depends(auth.require_role("admin")),
                     _csrf: None = Depends(csrf.require_valid)):
    with db.connect() as conn:
        target = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if target is None:
            raise HTTPException(status_code=404)
        if _would_drop_last_admin(conn, target, removing=True):
            return _render(request, user, error=LAST_ADMIN_ERROR, status_code=400)
        conn.execute("UPDATE users SET active = 0 WHERE id = ?", (user_id,))
        conn.commit()
    return RedirectResponse(url="/admin/users", status_code=303)
