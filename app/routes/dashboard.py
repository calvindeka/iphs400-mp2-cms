"""The dashboard (counts) and the combined, filterable Posts+Pages list.

CONTEXT.md "Content-list visibility": every admin/editor sees every item
regardless of author — "filter by author" is one filter dimension, not a
privacy wall.
"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from app import auth, csrf, db, settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES))


def _counts(conn: sqlite3.Connection) -> dict[str, int]:
    # `table` is always one of the two literals below — never request data —
    # so the f-string here can't be used to inject SQL.
    counts = {
        table: conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
        for table in ("posts", "pages")
    }
    counts["users"] = conn.execute(
        "SELECT COUNT(*) AS n FROM users WHERE active = 1"
    ).fetchone()["n"]
    return counts


def _query_posts(conn: sqlite3.Connection, status: str | None, category: str | None,
                  author: str | None) -> list[dict]:
    sql = ("SELECT p.id, p.title, p.slug, p.status, p.category, u.email AS author_email "
           "FROM posts p JOIN users u ON u.id = p.author_id WHERE 1=1")
    params: list[str] = []
    if status:
        sql += " AND p.status = ?"
        params.append(status)
    if category:
        sql += " AND p.category = ?"
        params.append(category)
    if author:
        sql += " AND u.email = ?"
        params.append(author)
    return [
        {"type": "post", "id": r["id"], "title": r["title"], "slug": r["slug"],
         "status": r["status"], "category": r["category"], "admin_only": None,
         "author_email": r["author_email"]}
        for r in conn.execute(sql, params).fetchall()
    ]


def _query_pages(conn: sqlite3.Connection, status: str | None, author: str | None) -> list[dict]:
    sql = ("SELECT pg.id, pg.title, pg.slug, pg.status, pg.admin_only, u.email AS author_email "
           "FROM pages pg JOIN users u ON u.id = pg.author_id WHERE 1=1")
    params: list[str] = []
    if status:
        sql += " AND pg.status = ?"
        params.append(status)
    if author:
        sql += " AND u.email = ?"
        params.append(author)
    return [
        {"type": "page", "id": r["id"], "title": r["title"], "slug": r["slug"],
         "status": r["status"], "category": None, "admin_only": bool(r["admin_only"]),
         "author_email": r["author_email"]}
        for r in conn.execute(sql, params).fetchall()
    ]


def content_rows(conn: sqlite3.Connection, type_: str | None = None, status: str | None = None,
                  category: str | None = None, author: str | None = None) -> list[dict]:
    """Posts and Pages, as one list of plain dicts (the two tables don't
    share every column, so sqlite3.Row objects can't be mixed directly)."""
    items: list[dict] = []
    if type_ in (None, "post"):
        items.extend(_query_posts(conn, status, category, author))
    # A category filter only matches Posts (Pages have no category). When no
    # type was chosen, a category filter implicitly means "posts," so pages
    # are correctly excluded — but an EXPLICIT type=page must still show
    # pages regardless of a stray category value, never silently empty.
    if type_ == "page" or (type_ is None and not category):
        items.extend(_query_pages(conn, status, author))
    return items


@router.get("/admin")
def dashboard(request: Request, user: auth.User = Depends(auth.require_login)):
    with db.connect() as conn:
        counts = _counts(conn)
    token = csrf.get_or_create_token(request)
    response = templates.TemplateResponse(
        request, "admin/hello.html",
        {"title": auth.console_label(user), "user": user, "csrf_token": token, "counts": counts},
    )
    csrf.apply_cookie(request, response, token)
    return response


@router.get("/admin/content")
def content_list(request: Request, type: str | None = None, status: str | None = None,
                  category: str | None = None, author: str | None = None,
                  user: auth.User = Depends(auth.require_login)):
    with db.connect() as conn:
        items = content_rows(conn, type, status, category, author)
    token = csrf.get_or_create_token(request)
    response = templates.TemplateResponse(
        request, "admin/content_list.html",
        {"title": "Content", "user": user, "items": items, "csrf_token": token,
         "filters": {"type": type, "status": status, "category": category, "author": author}},
    )
    csrf.apply_cookie(request, response, token)
    return response
