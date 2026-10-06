"""Shared test fixtures.

`client` gives you the app. `client_as(role)` gives you a client that is logged
in as a seeded user of that role — it works as soon as your login route exists,
so access-control tests stay one line:

    def test_editor_cannot_manage_users(client_as):
        assert client_as("editor").get("/admin/users").status_code in (302, 403)
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import settings
from app.main import create_app
from app.seed import DEMO_ACCOUNTS, seed_demo_users, seed_fixed_pages, seed_user

# Fixed, meaningless passwords for tests only — never read from the
# environment and never shared with scripts/seed_demo.py's real demo
# passwords (CLAUDE.md: "Read secrets from the environment").
TEST_PASSWORDS = {"admin": "test-admin-pw", "editor": "test-editor-pw"}

DEMO_USERS = {
    role: {"email": account["email"], "password": TEST_PASSWORDS[role]}
    for role, account in DEMO_ACCOUNTS.items()
}

# Pre-seeded inactive account, so tests of "deactivated user can't log in"
# only need an HTTP login attempt — no mid-test DB mutation.
DEACTIVATED_USER = {"email": "deactivated@example.test", "password": "test-deactivated-pw"}


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Every test gets its own fresh, pre-seeded database — never the real one."""
    monkeypatch.setattr(settings, "DATABASE_PATH", tmp_path / "test.db")
    seed_demo_users(TEST_PASSWORDS)
    seed_user(DEACTIVATED_USER["email"], DEACTIVATED_USER["password"], "editor", active=False)
    seed_fixed_pages(DEMO_ACCOUNTS["admin"]["email"])


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def client_as():
    """Return a factory: client_as("editor") -> a logged-in TestClient."""

    def _login(role: str) -> TestClient:
        user = DEMO_USERS[role]
        c = TestClient(create_app())
        response = c.post("/login", data={"email": user["email"],
                                          "password": user["password"]},
                          follow_redirects=False)
        if response.status_code == 404:
            pytest.skip("No /login route yet — build the login ticket first.")
        assert response.status_code in (200, 302, 303), (
            f"Login as {role} failed with {response.status_code}")
        return c

    return _login
