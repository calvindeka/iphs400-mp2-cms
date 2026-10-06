"""Page CRUD, plus the admin_only flag (CONTEXT.md: "admin_only (Page flag)").

Any logged-in user manages ordinary Pages; only admin can touch a Page
flagged admin_only (Membership), and only admin can set that flag in the
first place — a forged form field from an editor can't grant it.
"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app import auth, csrf, db, settings
from app.markdown import render_markdown
from app.slugs import unique_slug

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES))

STATUSES = {"draft", "published"}
# "posts" is reserved so a Page can never land on publish's posts/ directory
# (app/publish.py: Posts live under site/posts/<slug>/).
RESERVED_SLUGS = frozenset({"posts"})
SLUG_LOCKED_ERROR = "Can't change the slug of a published page."
INVALID_STATUS_ERROR = "Status must be draft or published."
RESERVED_SLUG_ERROR = '"posts" is a reserved slug and can\'t be used for a page.'
DUPLICATE_SLUG_ERROR = "That slug is already used by another page."


def _require_page_access(page, user: auth.User) -> None:
    if page["admin_only"] and user.role != "admin":
        raise HTTPException(status_code=403, detail="This page is admin-only")


def _render_list(request: Request, user: auth.User):
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM pages ORDER BY created_at DESC").fetchall()
    token = csrf.get_or_create_token(request)
    response = templates.TemplateResponse(
        request, "admin/pages_list.html",
        {"title": "Pages", "user": user, "pages": rows, "csrf_token": token},
    )
    csrf.apply_cookie(request, response, token)
    return response


def _render_form(request: Request, user: auth.User, page=None, error: str | None = None,
                  status_code: int = 200):
    token = csrf.get_or_create_token(request)
    response = templates.TemplateResponse(
        request, "admin/page_form.html",
        {"title": "Pages", "user": user, "page": page, "csrf_token": token, "error": error},
        status_code=status_code,
    )
    csrf.apply_cookie(request, response, token)
    return response


@router.get("/admin/pages")
def list_pages(request: Request, user: auth.User = Depends(auth.require_login)):
    return _render_list(request, user)


@router.get("/admin/pages/new")
def new_page_form(request: Request, user: auth.User = Depends(auth.require_login)):
    return _render_form(request, user)


@router.post("/admin/pages")
def create_page(request: Request, title: str = Form(...), body_md: str = Form(""),
                 admin_only: str = Form(""), user: auth.User = Depends(auth.require_login),
                 _csrf: None = Depends(csrf.require_valid)):
    is_admin_only = (admin_only == "on") and user.role == "admin"
    with db.connect() as conn:
        slug = unique_slug(conn, "pages", title, reserved=RESERVED_SLUGS)
        conn.execute(
            "INSERT INTO pages (title, slug, body_md, status, admin_only, author_id) "
            "VALUES (?, ?, ?, 'draft', ?, ?)",
            (title, slug, body_md, int(is_admin_only), user.id),
        )
        conn.commit()
    return RedirectResponse(url="/admin/pages", status_code=303)


@router.get("/admin/pages/{page_id}/edit")
def edit_page_form(request: Request, page_id: int, user: auth.User = Depends(auth.require_login)):
    with db.connect() as conn:
        page = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
    if page is None:
        raise HTTPException(status_code=404)
    _require_page_access(page, user)
    return _render_form(request, user, page=page)


@router.post("/admin/pages/{page_id}")
def update_page(request: Request, page_id: int, title: str = Form(...),
                 slug: str = Form(...), body_md: str = Form(""), status: str = Form(...),
                 admin_only: str = Form(""), user: auth.User = Depends(auth.require_login),
                 _csrf: None = Depends(csrf.require_valid)):
    with db.connect() as conn:
        page = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
        if page is None:
            raise HTTPException(status_code=404)
        _require_page_access(page, user)
        if status not in STATUSES:
            return _render_form(request, user, page=page, error=INVALID_STATUS_ERROR,
                                 status_code=400)
        if slug in RESERVED_SLUGS and slug != page["slug"]:
            return _render_form(request, user, page=page, error=RESERVED_SLUG_ERROR,
                                 status_code=400)

        # Same lock timing as Posts (CONTEXT.md "Slug lock"): bites once a
        # page IS already published, not on the exact request that first
        # publishes it.
        if page["status"] == "published" and slug != page["slug"]:
            return _render_form(request, user, page=page, error=SLUG_LOCKED_ERROR, status_code=400)

        is_admin_only = (admin_only == "on") if user.role == "admin" else bool(page["admin_only"])
        published_at = page["published_at"]
        if page["status"] == "draft" and status == "published":
            published_at = conn.execute("SELECT datetime('now') AS now").fetchone()["now"]

        try:
            conn.execute(
                "UPDATE pages SET title = ?, slug = ?, body_md = ?, status = ?, admin_only = ?, "
                "updated_at = datetime('now'), published_at = ? WHERE id = ?",
                (title, slug, body_md, status, int(is_admin_only), published_at, page_id),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return _render_form(request, user, page=page, error=DUPLICATE_SLUG_ERROR,
                                 status_code=400)
    return RedirectResponse(url="/admin/pages", status_code=303)


@router.get("/admin/pages/{page_id}/preview")
def preview_page(request: Request, page_id: int, user: auth.User = Depends(auth.require_login)):
    with db.connect() as conn:
        page = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
    if page is None:
        raise HTTPException(status_code=404)
    _require_page_access(page, user)
    return templates.TemplateResponse(
        request, "admin/preview.html",
        {"title": page["title"], "user": user, "body_html": render_markdown(page["body_md"]),
         "back_url": f"/admin/pages/{page_id}/edit"},
    )


@router.post("/admin/pages/{page_id}/delete")
def delete_page(request: Request, page_id: int, user: auth.User = Depends(auth.require_login),
                 _csrf: None = Depends(csrf.require_valid)):
    with db.connect() as conn:
        page = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
        if page is None:
            raise HTTPException(status_code=404)
        _require_page_access(page, user)
        conn.execute("DELETE FROM pages WHERE id = ?", (page_id,))
        conn.commit()
    return RedirectResponse(url="/admin/pages", status_code=303)
