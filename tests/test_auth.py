"""T01: login, logout, and the session/account-safety rules around them."""
from __future__ import annotations

from app import auth, db
from conftest import DEACTIVATED_USER, DEMO_USERS


def test_login_with_correct_credentials_sets_session_cookie(client):
    admin = DEMO_USERS["admin"]
    response = client.post(
        "/login", data={"email": admin["email"], "password": admin["password"]},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert auth.SESSION_COOKIE in response.cookies


def test_login_with_wrong_password_is_rejected(client):
    admin = DEMO_USERS["admin"]
    response = client.post(
        "/login", data={"email": admin["email"], "password": "not-the-password"},
    )
    assert response.status_code == 400
    assert auth.SESSION_COOKIE not in response.cookies


def test_wrong_password_message_matches_unknown_account_message(client):
    admin = DEMO_USERS["admin"]
    wrong_password = client.post(
        "/login", data={"email": admin["email"], "password": "not-the-password"},
    )
    unknown_account = client.post(
        "/login", data={"email": "nobody@example.test", "password": "whatever"},
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
    response = client.post(
        "/login", data={"email": DEACTIVATED_USER["email"],
                        "password": DEACTIVATED_USER["password"]},
    )
    assert response.status_code == 400
    assert auth.SESSION_COOKIE not in response.cookies


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
