"""Slug generation, shared by Posts and Pages (CONTEXT.md: "Slug lock").

A slug locks the moment its Post/Page is first published — this module only
makes a candidate slug; the lock rule itself lives in each route module,
since what "published" means differs slightly per content type's schema.
"""
from __future__ import annotations

import re
import sqlite3

_NON_SLUG = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    base = _NON_SLUG.sub("-", title.strip().lower()).strip("-")
    return base or "untitled"


def unique_slug(conn: sqlite3.Connection, table: str, title: str) -> str:
    base = slugify(title)
    slug = base
    n = 2
    while conn.execute(f"SELECT 1 FROM {table} WHERE slug = ?", (slug,)).fetchone():
        slug = f"{base}-{n}"
        n += 1
    return slug
