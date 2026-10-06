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
from app.slugs import slugify

DEMO_ACCOUNTS = {
    "admin": {"email": "admin@example.test", "role": "admin"},
    "editor": {"email": "editor@example.test", "role": "editor"},
}

# The four fixed Pages from CONTEXT.md. Membership is admin_only: "nobody
# but Tom edits the membership page" is a hard client rule.
FIXED_PAGES = [
    {"title": "About", "admin_only": False},
    {"title": "Dues", "admin_only": False},
    {"title": "Next Meeting", "admin_only": False},
    {"title": "Membership", "admin_only": True},
]


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


def seed_fixed_pages(author_email: str, path: Path | None = None) -> None:
    """Seed About, Dues, Next Meeting, Membership (admin_only), published."""
    db.init_db(path)
    with db.connect(path) as conn:
        author = conn.execute("SELECT id FROM users WHERE email = ?", (author_email,)).fetchone()
        for page in FIXED_PAGES:
            conn.execute(
                "INSERT OR IGNORE INTO pages "
                "(title, slug, body_md, status, admin_only, author_id, published_at) "
                "VALUES (?, ?, '', 'published', ?, ?, datetime('now'))",
                (page["title"], slugify(page["title"]), int(page["admin_only"]), author["id"]),
            )
        conn.commit()
