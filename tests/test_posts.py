"""T03: Post CRUD, slug auto-fill/lock, category, and draft privacy."""
from __future__ import annotations

from app import db


def _csrf_token(client):
    client.get("/admin/posts")
    return client.cookies["csrf_token"]


def _create_post(client, title="Fall Meeting Reminder", category="announcement", body_md="Hello."):
    token = _csrf_token(client)
    client.post("/admin/posts", data={
        "title": title, "body_md": body_md, "category": category, "csrf_token": token,
    })
    with db.connect() as conn:
        return conn.execute("SELECT * FROM posts WHERE title = ?", (title,)).fetchone()


def test_logged_in_user_can_create_a_post(client_as):
    post = _create_post(client_as("editor"))
    assert post is not None
    assert post["status"] == "draft"


def test_slug_auto_fills_from_title(client_as):
    post = _create_post(client_as("editor"))
    assert post["slug"] == "fall-meeting-reminder"


def test_category_is_stored_and_retrievable(client_as):
    post = _create_post(client_as("editor"), category="research")
    assert post["category"] == "research"


def test_logged_in_user_can_read_update_and_delete_a_post(client_as):
    editor = client_as("editor")
    post = _create_post(editor)

    assert editor.get(f"/admin/posts/{post['id']}/edit").status_code == 200

    token = _csrf_token(editor)
    update = editor.post(f"/admin/posts/{post['id']}", data={
        "title": "Updated title", "slug": post["slug"], "body_md": "New body.",
        "category": "announcement", "status": "draft", "csrf_token": token,
    }, follow_redirects=False)
    assert update.status_code == 303
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (post["id"],)).fetchone()
    assert row["title"] == "Updated title" and row["body_md"] == "New body."

    token = _csrf_token(editor)
    delete = editor.post(f"/admin/posts/{post['id']}/delete",
                          data={"csrf_token": token}, follow_redirects=False)
    assert delete.status_code == 303
    with db.connect() as conn:
        assert conn.execute("SELECT 1 FROM posts WHERE id = ?", (post["id"],)).fetchone() is None


def test_slug_is_editable_while_draft(client_as):
    editor = client_as("editor")
    post = _create_post(editor)
    token = _csrf_token(editor)
    response = editor.post(f"/admin/posts/{post['id']}", data={
        "title": post["title"], "slug": "a-new-slug", "body_md": post["body_md"],
        "category": post["category"], "status": "draft", "csrf_token": token,
    }, follow_redirects=False)
    assert response.status_code == 303
    with db.connect() as conn:
        row = conn.execute("SELECT slug FROM posts WHERE id = ?", (post["id"],)).fetchone()
    assert row["slug"] == "a-new-slug"


def test_slug_change_is_rejected_once_published(client_as):
    editor = client_as("editor")
    post = _create_post(editor)
    token = _csrf_token(editor)
    editor.post(f"/admin/posts/{post['id']}", data={
        "title": post["title"], "slug": post["slug"], "body_md": post["body_md"],
        "category": post["category"], "status": "published", "csrf_token": token,
    })

    token = _csrf_token(editor)
    response = editor.post(f"/admin/posts/{post['id']}", data={
        "title": post["title"], "slug": "trying-to-change-this", "body_md": post["body_md"],
        "category": post["category"], "status": "published", "csrf_token": token,
    })
    assert response.status_code == 400
    with db.connect() as conn:
        row = conn.execute("SELECT slug, published_at FROM posts WHERE id = ?", (post["id"],)).fetchone()
    assert row["slug"] == post["slug"]
    assert row["published_at"] is not None


def test_draft_post_is_not_reachable_by_anonymous_get(client_as, client):
    post = _create_post(client_as("editor"))
    response = client.get(f"/admin/posts/{post['id']}/edit", follow_redirects=False)
    assert response.status_code in (302, 303)


def test_anonymous_cannot_list_posts(client):
    response = client.get("/admin/posts", follow_redirects=False)
    assert response.status_code in (302, 303)


def test_create_post_rejects_an_invalid_category(client_as):
    editor = client_as("editor")
    token = _csrf_token(editor)
    response = editor.post("/admin/posts", data={
        "title": "Bad Category", "body_md": "", "category": "gossip", "csrf_token": token,
    })
    assert response.status_code == 400
    with db.connect() as conn:
        assert conn.execute("SELECT 1 FROM posts WHERE title = ?", ("Bad Category",)).fetchone() is None


def test_update_post_rejects_a_duplicate_slug(client_as):
    editor = client_as("editor")
    first = _create_post(editor, title="First Post")
    second = _create_post(editor, title="Second Post")

    token = _csrf_token(editor)
    response = editor.post(f"/admin/posts/{second['id']}", data={
        "title": second["title"], "slug": first["slug"], "body_md": second["body_md"],
        "category": second["category"], "status": "draft", "csrf_token": token,
    })
    assert response.status_code == 400
    with db.connect() as conn:
        row = conn.execute("SELECT slug FROM posts WHERE id = ?", (second["id"],)).fetchone()
    assert row["slug"] == second["slug"]


def test_update_post_rejects_an_invalid_status(client_as):
    editor = client_as("editor")
    post = _create_post(editor)
    token = _csrf_token(editor)
    response = editor.post(f"/admin/posts/{post['id']}", data={
        "title": post["title"], "slug": post["slug"], "body_md": post["body_md"],
        "category": post["category"], "status": "archived", "csrf_token": token,
    })
    assert response.status_code == 400
    with db.connect() as conn:
        row = conn.execute("SELECT status FROM posts WHERE id = ?", (post["id"],)).fetchone()
    assert row["status"] == "draft"


def test_delete_post_404s_on_a_missing_id(client_as):
    editor = client_as("editor")
    token = _csrf_token(editor)
    response = editor.post("/admin/posts/999999/delete", data={"csrf_token": token})
    assert response.status_code == 404


def test_slug_may_change_on_the_exact_request_that_first_publishes_a_post(client_as):
    """The lock (CONTEXT.md "Slug lock") bites once a post IS published —
    not on the request that performs that first publish."""
    editor = client_as("editor")
    post = _create_post(editor)
    token = _csrf_token(editor)
    response = editor.post(f"/admin/posts/{post['id']}", data={
        "title": post["title"], "slug": "final-slug-at-publish-time", "body_md": post["body_md"],
        "category": post["category"], "status": "published", "csrf_token": token,
    }, follow_redirects=False)
    assert response.status_code == 303
    with db.connect() as conn:
        row = conn.execute("SELECT slug FROM posts WHERE id = ?", (post["id"],)).fetchone()
    assert row["slug"] == "final-slug-at-publish-time"
