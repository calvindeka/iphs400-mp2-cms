"""T04: Page CRUD, the admin_only flag, slug lock, and fixed seed pages."""
from __future__ import annotations

from app import db


def _csrf_token(client):
    client.get("/admin/pages")
    return client.cookies["csrf_token"]


def _create_page(client, title="Volunteer Schedule", body_md="Hello."):
    token = _csrf_token(client)
    client.post("/admin/pages", data={"title": title, "body_md": body_md, "csrf_token": token})
    with db.connect() as conn:
        return conn.execute("SELECT * FROM pages WHERE title = ?", (title,)).fetchone()


def test_logged_in_user_can_create_read_update_delete_a_page(client_as):
    editor = client_as("editor")
    page = _create_page(editor)
    assert page is not None and page["status"] == "draft" and not page["admin_only"]

    assert editor.get(f"/admin/pages/{page['id']}/edit").status_code == 200

    token = _csrf_token(editor)
    update = editor.post(f"/admin/pages/{page['id']}", data={
        "title": "Updated", "slug": page["slug"], "body_md": "New body.",
        "status": "draft", "csrf_token": token,
    }, follow_redirects=False)
    assert update.status_code == 303
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM pages WHERE id = ?", (page["id"],)).fetchone()
    assert row["title"] == "Updated"

    token = _csrf_token(editor)
    delete = editor.post(f"/admin/pages/{page['id']}/delete",
                          data={"csrf_token": token}, follow_redirects=False)
    assert delete.status_code == 303


def test_slug_locks_on_first_publish_same_as_posts(client_as):
    editor = client_as("editor")
    page = _create_page(editor)
    token = _csrf_token(editor)
    editor.post(f"/admin/pages/{page['id']}", data={
        "title": page["title"], "slug": page["slug"], "body_md": page["body_md"],
        "status": "published", "csrf_token": token,
    })

    token = _csrf_token(editor)
    response = editor.post(f"/admin/pages/{page['id']}", data={
        "title": page["title"], "slug": "trying-to-change", "body_md": page["body_md"],
        "status": "published", "csrf_token": token,
    })
    assert response.status_code == 400
    with db.connect() as conn:
        row = conn.execute("SELECT slug FROM pages WHERE id = ?", (page["id"],)).fetchone()
    assert row["slug"] == page["slug"]


def test_slug_may_change_on_the_exact_request_that_first_publishes_a_page(client_as):
    editor = client_as("editor")
    page = _create_page(editor)
    token = _csrf_token(editor)
    response = editor.post(f"/admin/pages/{page['id']}", data={
        "title": page["title"], "slug": "final-slug-at-publish-time", "body_md": page["body_md"],
        "status": "published", "csrf_token": token,
    }, follow_redirects=False)
    assert response.status_code == 303
    with db.connect() as conn:
        row = conn.execute("SELECT slug FROM pages WHERE id = ?", (page["id"],)).fetchone()
    assert row["slug"] == "final-slug-at-publish-time"


def test_update_page_rejects_an_invalid_status(client_as):
    editor = client_as("editor")
    page = _create_page(editor)
    token = _csrf_token(editor)
    response = editor.post(f"/admin/pages/{page['id']}", data={
        "title": page["title"], "slug": page["slug"], "body_md": page["body_md"],
        "status": "archived", "csrf_token": token,
    })
    assert response.status_code == 400


def test_editor_cannot_edit_or_delete_an_admin_only_page(client_as):
    editor = client_as("editor")
    with db.connect() as conn:
        membership = conn.execute("SELECT * FROM pages WHERE title = 'Membership'").fetchone()

    assert editor.get(f"/admin/pages/{membership['id']}/edit").status_code == 403

    token = _csrf_token(editor)
    response = editor.post(f"/admin/pages/{membership['id']}", data={
        "title": "Hijacked", "slug": membership["slug"], "body_md": "",
        "status": membership["status"], "csrf_token": token,
    })
    assert response.status_code == 403

    response = editor.post(f"/admin/pages/{membership['id']}/delete",
                            data={"csrf_token": token})
    assert response.status_code == 403


def test_admin_can_edit_and_delete_an_admin_only_page(client_as):
    admin = client_as("admin")
    with db.connect() as conn:
        membership = conn.execute("SELECT * FROM pages WHERE title = 'Membership'").fetchone()

    assert admin.get(f"/admin/pages/{membership['id']}/edit").status_code == 200

    token = _csrf_token(admin)
    response = admin.post(f"/admin/pages/{membership['id']}", data={
        "title": "Membership", "slug": membership["slug"], "body_md": "Updated.",
        "status": membership["status"], "csrf_token": token,
    }, follow_redirects=False)
    assert response.status_code == 303


def test_a_non_admin_only_page_is_editable_by_any_editor(client_as):
    editor = client_as("editor")
    with db.connect() as conn:
        about = conn.execute("SELECT * FROM pages WHERE title = 'About'").fetchone()
    assert editor.get(f"/admin/pages/{about['id']}/edit").status_code == 200


def test_editor_cannot_create_an_admin_only_page(client_as):
    editor = client_as("editor")
    token = _csrf_token(editor)
    editor.post("/admin/pages", data={
        "title": "Sneaky Admin Page", "body_md": "", "admin_only": "on", "csrf_token": token,
    })
    with db.connect() as conn:
        row = conn.execute(
            "SELECT admin_only FROM pages WHERE title = ?", ("Sneaky Admin Page",)
        ).fetchone()
    assert row["admin_only"] == 0


def test_seed_data_includes_the_four_fixed_pages():
    with db.connect() as conn:
        titles = {r["title"] for r in conn.execute("SELECT title FROM pages").fetchall()}
        membership = conn.execute("SELECT admin_only FROM pages WHERE title = 'Membership'").fetchone()
    assert titles == {"About", "Dues", "Next Meeting", "Membership"}
    assert membership["admin_only"] == 1


def test_draft_page_is_not_reachable_by_anonymous_get(client_as, client):
    page = _create_page(client_as("editor"))
    response = client.get(f"/admin/pages/{page['id']}/edit", follow_redirects=False)
    assert response.status_code in (302, 303)
