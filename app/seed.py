"""Demo-user seeding, shared by scripts/seed_demo.py and the test suite.

Passwords are never hardcoded here (CLAUDE.md: "Read secrets from the
environment") — callers supply them. scripts/seed_demo.py reads real demo
passwords from the environment; tests/conftest.py uses its own fixed,
meaningless test passwords. Only email/role are shared, since those aren't
secrets.
"""
from __future__ import annotations

from pathlib import Path

from app import auth, db

DEMO_ACCOUNTS = {
    "admin": {"email": "admin@example.test", "role": "admin"},
    "editor": {"email": "editor@example.test", "role": "editor"},
}


def seed_user(email: str, password: str, role: str, active: bool = True,
              path: Path | None = None) -> None:
    db.init_db(path)
    with db.connect(path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (email, password_hash, role, active) "
            "VALUES (?, ?, ?, ?)",
            (email, auth.hash_password(password), role, int(active)),
        )
        conn.commit()


def seed_demo_users(passwords: dict[str, str], path: Path | None = None) -> None:
    """Seed the demo admin/editor. `passwords` maps role -> plaintext password."""
    for role, account in DEMO_ACCOUNTS.items():
        seed_user(account["email"], passwords[role], account["role"], path=path)
