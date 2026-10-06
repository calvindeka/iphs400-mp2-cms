#!/usr/bin/env python3
"""Seed demo users into the local database.

    uv run python scripts/seed_demo.py

Reads CMS_ADMIN_PASSWORD and CMS_EDITOR_PASSWORD from the environment (copy
.env.example to .env) — passwords are never hard-coded in source, and the
database itself is gitignored.
"""
from __future__ import annotations

import os
import sys

from app import settings
from app.seed import DEMO_ACCOUNTS, seed_demo_users, seed_fixed_pages


def main() -> int:
    admin_pw = os.environ.get("CMS_ADMIN_PASSWORD")
    editor_pw = os.environ.get("CMS_EDITOR_PASSWORD")
    if not admin_pw or not editor_pw:
        print("Set CMS_ADMIN_PASSWORD and CMS_EDITOR_PASSWORD in .env "
              "(copy .env.example).")
        return 1

    seed_demo_users({"admin": admin_pw, "editor": editor_pw})
    seed_fixed_pages(DEMO_ACCOUNTS["admin"]["email"])
    print(f"Seeded demo users and fixed pages into {settings.DATABASE_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
