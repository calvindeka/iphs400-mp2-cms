"""Post CRUD. Any logged-in admin/editor can manage any Post (CONTEXT.md:
"Content-list visibility" — no per-author wall)."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app import auth, csrf, db, settings
from app.slugs import unique_slug

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES))

CATEGORIES = {"announcement", "research"}
STATUSES = {"draft", "published"}
SLUG_LOCKED_ERROR = "Can't change the slug of a published post."
INVALID_CATEGORY_ERROR = "Category must be announcement or research."
INVALID_STATUS_ERROR = "Status must be draft or published."
DUPLICATE_SLUG_ERROR = "That slug is already used by another post."


def _render_list(request: Request, user: auth.User):
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM posts ORDER BY created_at DESC").fetchall()
    token = csrf.get_or_create_token(request)
    response = templates.TemplateResponse(
        request, "admin/posts_list.html",
        {"title": "Posts", "user": user, "posts": rows, "csrf_token": token},
    )
    csrf.apply_cookie(request, response, token)
    return response


def _render_form(request: Request, user: auth.User, post=None, error: str | None = None,
                  status_code: int = 200):
    token = csrf.get_or_create_token(request)
    response = templates.TemplateResponse(
        request, "admin/post_form.html",
        {"title": "Posts", "user": user, "post": post, "csrf_token": token, "error": error},
        status_code=status_code,
    )
    csrf.apply_cookie(request, response, token)
    return response


@router.get("/admin/posts")
def list_posts(request: Request, user: auth.User = Depends(auth.require_login)):
    return _render_list(request, user)


@router.get("/admin/posts/new")
def new_post_form(request: Request, user: auth.User = Depends(auth.require_login)):
    return _render_form(request, user)


@router.post("/admin/posts")
def create_post(request: Request, title: str = Form(...), body_md: str = Form(""),
                 category: str = Form(...), user: auth.User = Depends(auth.require_login),
                 _csrf: None = Depends(csrf.require_valid)):
    if category not in CATEGORIES:
        return _render_form(request, user, error=INVALID_CATEGORY_ERROR, status_code=400)
    with db.connect() as conn:
        slug = unique_slug(conn, "posts", title)
        conn.execute(
            "INSERT INTO posts (title, slug, body_md, category, status, author_id) "
            "VALUES (?, ?, ?, ?, 'draft', ?)",
            (title, slug, body_md, category, user.id),
        )
        conn.commit()
    return RedirectResponse(url="/admin/posts", status_code=303)


@router.get("/admin/posts/{post_id}/edit")
def edit_post_form(request: Request, post_id: int, user: auth.User = Depends(auth.require_login)):
    with db.connect() as conn:
        post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        raise HTTPException(status_code=404)
    return _render_form(request, user, post=post)


@router.post("/admin/posts/{post_id}")
def update_post(request: Request, post_id: int, title: str = Form(...),
                 slug: str = Form(...), body_md: str = Form(""), category: str = Form(...),
                 status: str = Form(...), user: auth.User = Depends(auth.require_login),
                 _csrf: None = Depends(csrf.require_valid)):
    with db.connect() as conn:
        post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if post is None:
            raise HTTPException(status_code=404)

        if category not in CATEGORIES:
            return _render_form(request, user, post=post, error=INVALID_CATEGORY_ERROR,
                                 status_code=400)
        if status not in STATUSES:
            return _render_form(request, user, post=post, error=INVALID_STATUS_ERROR,
                                 status_code=400)

        # The lock bites once a post IS published (before this request); the
        # exact request that first publishes it may still set the slug it
        # locks in — see CONTEXT.md "Slug lock".
        if post["status"] == "published" and slug != post["slug"]:
            return _render_form(request, user, post=post, error=SLUG_LOCKED_ERROR, status_code=400)

        published_at = post["published_at"]
        if post["status"] == "draft" and status == "published":
            published_at = conn.execute("SELECT datetime('now') AS now").fetchone()["now"]

        try:
            conn.execute(
                "UPDATE posts SET title = ?, slug = ?, body_md = ?, category = ?, status = ?, "
                "updated_at = datetime('now'), published_at = ? WHERE id = ?",
                (title, slug, body_md, category, status, published_at, post_id),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return _render_form(request, user, post=post, error=DUPLICATE_SLUG_ERROR,
                                 status_code=400)
    return RedirectResponse(url="/admin/posts", status_code=303)


@router.post("/admin/posts/{post_id}/delete")
def delete_post(request: Request, post_id: int, user: auth.User = Depends(auth.require_login),
                 _csrf: None = Depends(csrf.require_valid)):
    with db.connect() as conn:
        if conn.execute("SELECT 1 FROM posts WHERE id = ?", (post_id,)).fetchone() is None:
            raise HTTPException(status_code=404)
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
    return RedirectResponse(url="/admin/posts", status_code=303)
