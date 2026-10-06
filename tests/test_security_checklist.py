"""T07: systematic verification against every SECURITY-CHECKLIST.md item.

Most items already have a test elsewhere (see the comment on issue #8 for
the full map); this file closes the gaps that weren't yet covered anywhere:
CSRF-token-removed on every single state-changing route (#3), and the
preview-side half of the Markdown-injection check (#7).
"""
from __future__ import annotations

from app import db
from app.markdown import render_markdown


def _seed_ids():
    with db.connect() as conn:
        about = conn.execute("SELECT id FROM pages WHERE slug = 'about'").fetchone()["id"]
    return about


def _create_post(client):
    client.get("/admin/posts")
    token = client.cookies["csrf_token"]
    client.post("/admin/posts", data={
        "title": "CSRF Fixture Post", "body_md": "x", "category": "announcement",
        "csrf_token": token,
    })
    with db.connect() as conn:
        return conn.execute(
            "SELECT id FROM posts WHERE title = 'CSRF Fixture Post'"
        ).fetchone()["id"]


# Checklist #3: "Every state-changing form (POST) carries a CSRF token and
# rejects a request without one" — "replays each POST with the token
# removed." Checked against every single mutating route in the app
# (cross-referenced against every @router.post in app/routes/*.py), not
# just a sample. Omitting the csrf_token field entirely makes FastAPI's own
# required-Form-field validation reject with 422, before our route body (or
# csrf.require_valid's check) ever runs — asserting the exact code, not just
# "not success", so a future refactor that moved a mutation earlier would
# fail this test instead of slipping through.
def test_every_state_changing_post_rejects_a_request_with_no_csrf_token(client_as):
    admin = client_as("admin")
    with db.connect() as conn:
        editor_id = conn.execute(
            "SELECT id FROM users WHERE email = 'editor@example.test'"
        ).fetchone()["id"]
    page_id = _seed_ids()
    post_id = _create_post(admin)

    routes = [
        ("/admin/users", {"email": "nobody@example.test", "password": "x", "role": "editor"}),
        (f"/admin/users/{editor_id}/role", {"role": "admin"}),
        (f"/admin/users/{editor_id}/deactivate", {}),
        ("/admin/posts", {"title": "x", "body_md": "x", "category": "announcement"}),
        (f"/admin/posts/{post_id}", {"title": "Renamed", "slug": "x", "body_md": "x",
                                      "category": "announcement", "status": "draft"}),
        (f"/admin/posts/{post_id}/delete", {}),
        ("/admin/pages", {"title": "x", "body_md": "x"}),
        (f"/admin/pages/{page_id}", {"title": "Renamed", "slug": "about", "body_md": "x",
                                      "status": "published"}),
        (f"/admin/pages/{page_id}/delete", {}),
        ("/logout", {}),
    ]
    for path, data in routes:
        response = admin.post(path, data=data, follow_redirects=False)
        assert response.status_code == 422, f"{path} returned {response.status_code}, expected 422"

    # Spot-check every mutation attempted above was actually rejected, not applied.
    with db.connect() as conn:
        assert conn.execute(
            "SELECT 1 FROM users WHERE email = 'nobody@example.test'"
        ).fetchone() is None
        assert conn.execute(
            "SELECT role FROM users WHERE id = ?", (editor_id,)
        ).fetchone()["role"] == "editor"
        assert conn.execute(
            "SELECT active FROM users WHERE id = ?", (editor_id,)
        ).fetchone()["active"] == 1
        assert conn.execute(
            "SELECT title FROM posts WHERE id = ?", (post_id,)
        ).fetchone()["title"] == "CSRF Fixture Post"
        assert conn.execute("SELECT title FROM pages WHERE id = ?", (page_id,)).fetchone()["title"] == "About"
        assert conn.execute("SELECT 1 FROM pages WHERE id = ?", (page_id,)).fetchone() is not None


# Checklist #7, preview half: "Saves a post containing <script> and an
# onerror= attribute, publishes, and checks both the preview and the
# export." test_publish.py covers the export; this covers the preview.
def test_preview_strips_script_and_onerror_from_injected_markdown(client_as):
    editor = client_as("editor")
    payload = '<script>alert(1)</script><img src="x" onerror="alert(1)">'
    editor.get("/admin/posts")
    token = editor.cookies["csrf_token"]
    editor.post("/admin/posts", data={
        "title": "Injection Preview Post", "body_md": payload,
        "category": "announcement", "csrf_token": token,
    })
    with db.connect() as conn:
        post_id = conn.execute(
            "SELECT id FROM posts WHERE title = 'Injection Preview Post'"
        ).fetchone()["id"]

    response = editor.get(f"/admin/posts/{post_id}/preview")
    assert "<script" not in response.text
    assert "onerror" not in response.text


def test_render_markdown_strips_script_and_onerror_directly():
    """A direct unit check on the one function every render path shares."""
    html = render_markdown('<script>alert(1)</script><img src="x" onerror="alert(1)">')
    assert "<script" not in html
    assert "onerror" not in html


# Checklist #5: "An anonymous visitor is redirected to login, never shown
# admin content" — swept across every GET-able admin route, not just /admin.
def test_anonymous_is_redirected_from_every_admin_route(client):
    admin_routes = [
        "/admin", "/admin/content", "/admin/users",
        "/admin/posts", "/admin/posts/new",
        "/admin/pages", "/admin/pages/new",
    ]
    for path in admin_routes:
        response = client.get(path, follow_redirects=False)
        assert response.status_code in (302, 303), f"{path} did not redirect an anonymous visitor"
        assert response.headers["location"].endswith("/login")
