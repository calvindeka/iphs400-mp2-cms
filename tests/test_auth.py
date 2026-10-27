"""T01: login, logout, and the session/account-safety rules around them."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from app import auth, db
from conftest import DEACTIVATED_USER, DEMO_USERS

ROOT = Path(__file__).resolve().parents[1]


def test_login_with_correct_credentials_sets_session_cookie(client):
    admin = DEMO_USERS["admin"]
    client.get("/login")  # issues the CSRF cookie the login form needs
    csrf_token = client.cookies["csrf_token"]
    response = client.post(
        "/login", data={"email": admin["email"], "password": admin["password"],
                        "csrf_token": csrf_token},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert auth.SESSION_COOKIE in response.cookies


def test_login_with_wrong_password_is_rejected(client):
    admin = DEMO_USERS["admin"]
    client.get("/login")
    csrf_token = client.cookies["csrf_token"]
    response = client.post(
        "/login", data={"email": admin["email"], "password": "not-the-password",
                        "csrf_token": csrf_token},
    )
    assert response.status_code == 400
    assert auth.SESSION_COOKIE not in response.cookies


def test_login_without_csrf_token_is_rejected(client):
    admin = DEMO_USERS["admin"]
    response = client.post(
        "/login", data={"email": admin["email"], "password": admin["password"]},
    )
    assert response.status_code == 422
    assert auth.SESSION_COOKIE not in response.cookies


def test_login_with_forged_csrf_token_is_rejected(client):
    admin = DEMO_USERS["admin"]
    client.get("/login")
    response = client.post(
        "/login", data={"email": admin["email"], "password": admin["password"],
                        "csrf_token": "forged"},
    )
    assert response.status_code == 400
    assert auth.SESSION_COOKIE not in response.cookies


def test_wrong_password_message_matches_unknown_account_message(client):
    admin = DEMO_USERS["admin"]
    client.get("/login")
    csrf_token = client.cookies["csrf_token"]
    wrong_password = client.post(
        "/login", data={"email": admin["email"], "password": "not-the-password",
                        "csrf_token": csrf_token},
    )
    unknown_account = client.post(
        "/login", data={"email": "nobody@example.test", "password": "whatever",
                        "csrf_token": csrf_token},
    )
    assert wrong_password.text == unknown_account.text


def test_logout_clears_session(client_as):
    logged_in = client_as("admin")
    logged_in.get("/admin")  # issues the CSRF cookie the logout form needs
    csrf_token = logged_in.cookies["csrf_token"]

    response = logged_in.post("/logout", data={"csrf_token": csrf_token}, follow_redirects=False)
    assert response.status_code == 303
    assert logged_in.get("/admin", follow_redirects=False).status_code in (302, 303)


def test_logout_without_csrf_token_is_rejected(client_as):
    logged_in = client_as("admin")
    logged_in.get("/admin")

    response = logged_in.post("/logout", data={"csrf_token": "forged"}, follow_redirects=False)
    assert response.status_code == 400
    # the session survives an invalid logout attempt
    assert logged_in.get("/admin", follow_redirects=False).status_code == 200


def test_deactivated_user_cannot_log_in(client):
    client.get("/login")
    csrf_token = client.cookies["csrf_token"]
    response = client.post(
        "/login", data={"email": DEACTIVATED_USER["email"],
                        "password": DEACTIVATED_USER["password"],
                        "csrf_token": csrf_token},
    )
    assert response.status_code == 400
    assert auth.SESSION_COOKIE not in response.cookies


def test_seed_demo_script_seeds_the_demo_users_conftest_expects(tmp_path):
    """Runs the real script scripts/seed_demo.py, not app.seed directly, with
    the exact values .env.example documents — the gap conftest.py's own
    seeding (via app.seed, its own passwords) doesn't cover."""
    db_path = tmp_path / "cms.db"
    env = {**os.environ, "CMS_DATABASE": str(db_path),
           "CMS_ADMIN_PASSWORD": "change-me-admin",
           "CMS_EDITOR_PASSWORD": "change-me-editor"}
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "seed_demo.py")],
        env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr

    with db.connect(db_path) as conn:
        rows = conn.execute("SELECT email, role, password_hash FROM users ORDER BY email").fetchall()
    assert [r["email"] for r in rows] == ["admin@example.test", "editor@example.test"]
    assert [r["role"] for r in rows] == ["admin", "editor"]
    assert all(r["password_hash"].startswith("$argon2") for r in rows)


def test_passwords_are_stored_as_argon2_hashes_not_plaintext():
    """The one deliberate exception to the HTTP-only seam: hashing can't be
    observed over HTTP, so this reads the seeded database directly."""
    with db.connect() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            (DEMO_USERS["admin"]["email"],),
        ).fetchone()
    assert row["password_hash"] != DEMO_USERS["admin"]["password"]
    assert row["password_hash"].startswith("$argon2")
