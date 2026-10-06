"""T02: admin-only user management, role-gating, and the last-admin guard."""
from __future__ import annotations

import re

from app import db
from conftest import DEMO_USERS


def _visible_text(html: str) -> str:
    """Strip tags/attributes so a check doesn't trip on URL paths like /admin/posts."""
    return re.sub(r"<[^>]+>", " ", html)


def _csrf_token(client):
    client.get("/admin/users")
    return client.cookies["csrf_token"]


def test_admin_can_create_a_user(client_as):
    admin = client_as("admin")
    token = _csrf_token(admin)
    response = admin.post(
        "/admin/users",
        data={"email": "priya@example.test", "password": "priya-initial-pw",
              "role": "editor", "csrf_token": token},
        follow_redirects=False,
    )
    assert response.status_code == 303
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", ("priya@example.test",)).fetchone()
    assert row is not None and row["role"] == "editor" and row["active"]


def test_editor_cannot_reach_admin_only_user_routes(client_as):
    editor = client_as("editor")
    assert editor.get("/admin/users").status_code == 403


def test_anonymous_cannot_reach_admin_only_user_routes(client):
    response = client.get("/admin/users", follow_redirects=False)
    assert response.status_code in (302, 303)


def test_editor_cannot_create_a_user(client_as):
    editor = client_as("editor")
    response = editor.post("/admin/users", data={
        "email": "sneaky@example.test", "password": "x", "role": "editor",
        "csrf_token": "whatever",
    })
    assert response.status_code == 403


def test_editor_cannot_change_a_role(client_as):
    editor = client_as("editor")
    response = editor.post(f"/admin/users/{_admin_id()}/role", data={
        "role": "editor", "csrf_token": "whatever",
    })
    assert response.status_code == 403


def test_editor_cannot_deactivate_a_user(client_as):
    editor = client_as("editor")
    response = editor.post(f"/admin/users/{_admin_id()}/deactivate", data={
        "csrf_token": "whatever",
    })
    assert response.status_code == 403


def test_anonymous_cannot_create_a_user(client):
    response = client.post("/admin/users", data={
        "email": "sneaky@example.test", "password": "x", "role": "editor",
        "csrf_token": "whatever",
    }, follow_redirects=False)
    assert response.status_code in (302, 303)


def test_admin_can_change_a_users_role(client_as):
    admin = client_as("admin")
    editor_id = _editor_id()
    token = _csrf_token(admin)
    response = admin.post(f"/admin/users/{editor_id}/role",
                           data={"role": "admin", "csrf_token": token}, follow_redirects=False)
    assert response.status_code == 303
    with db.connect() as conn:
        row = conn.execute("SELECT role FROM users WHERE id = ?", (editor_id,)).fetchone()
    assert row["role"] == "admin"


def test_admin_can_deactivate_a_user(client_as):
    admin = client_as("admin")
    editor_id = _editor_id()
    token = _csrf_token(admin)
    response = admin.post(f"/admin/users/{editor_id}/deactivate",
                           data={"csrf_token": token}, follow_redirects=False)
    assert response.status_code == 303
    with db.connect() as conn:
        row = conn.execute("SELECT active FROM users WHERE id = ?", (editor_id,)).fetchone()
    assert row["active"] == 0


def test_demoting_the_last_admin_is_rejected(client_as):
    admin = client_as("admin")
    admin_id = _admin_id()
    token = _csrf_token(admin)
    response = admin.post(f"/admin/users/{admin_id}/role",
                           data={"role": "editor", "csrf_token": token})
    assert response.status_code == 400
    with db.connect() as conn:
        row = conn.execute("SELECT role FROM users WHERE id = ?", (admin_id,)).fetchone()
    assert row["role"] == "admin"


def test_deactivating_the_last_admin_is_rejected(client_as):
    admin = client_as("admin")
    admin_id = _admin_id()
    token = _csrf_token(admin)
    response = admin.post(f"/admin/users/{admin_id}/deactivate",
                           data={"csrf_token": token})
    assert response.status_code == 400
    with db.connect() as conn:
        row = conn.execute("SELECT active FROM users WHERE id = ?", (admin_id,)).fetchone()
    assert row["active"] == 1


def test_demoting_a_second_admin_is_allowed(client_as):
    """The guard only blocks reaching zero active admins, not having two."""
    admin = client_as("admin")
    token = _csrf_token(admin)
    admin.post("/admin/users", data={"email": "second-admin@example.test",
                                      "password": "second-admin-pw", "role": "admin",
                                      "csrf_token": token})
    with db.connect() as conn:
        second_id = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("second-admin@example.test",)
        ).fetchone()["id"]

    token = _csrf_token(admin)
    response = admin.post(f"/admin/users/{second_id}/role",
                           data={"role": "editor", "csrf_token": token}, follow_redirects=False)
    assert response.status_code == 303


def test_create_user_rejects_an_invalid_role(client_as):
    admin = client_as("admin")
    token = _csrf_token(admin)
    response = admin.post("/admin/users", data={
        "email": "new@example.test", "password": "x", "role": "superuser",
        "csrf_token": token,
    })
    assert response.status_code == 400
    with db.connect() as conn:
        assert conn.execute("SELECT 1 FROM users WHERE email = ?", ("new@example.test",)).fetchone() is None


def test_create_user_rejects_a_duplicate_email(client_as):
    admin = client_as("admin")
    token = _csrf_token(admin)
    response = admin.post("/admin/users", data={
        "email": DEMO_USERS["editor"]["email"], "password": "x", "role": "editor",
        "csrf_token": token,
    })
    assert response.status_code == 400


def test_editor_role_ui_chrome_avoids_the_word_admin(client_as):
    response = client_as("editor").get("/admin")
    assert "admin" not in _visible_text(response.text).lower()


def test_admin_role_ui_chrome_shows_admin_language(client_as):
    response = client_as("admin").get("/admin")
    assert "admin" in _visible_text(response.text).lower()


def _editor_id() -> int:
    with db.connect() as conn:
        return conn.execute(
            "SELECT id FROM users WHERE email = ?", (DEMO_USERS["editor"]["email"],)
        ).fetchone()["id"]


def _admin_id() -> int:
    with db.connect() as conn:
        return conn.execute(
            "SELECT id FROM users WHERE email = ?", (DEMO_USERS["admin"]["email"],)
        ).fetchone()["id"]
