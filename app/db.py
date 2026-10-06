"""SQLite connection and schema. One file, per ADR-002: no ORM, no server.

Each ticket extends SCHEMA with its own tables as it needs them. T01 only
needs users; T03/T04 add posts/pages later.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'editor')),
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    body_md TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL CHECK (category IN ('announcement', 'research')),
    status TEXT NOT NULL CHECK (status IN ('draft', 'published')) DEFAULT 'draft',
    author_id INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    published_at TEXT
);

CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    body_md TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('draft', 'published')) DEFAULT 'draft',
    admin_only INTEGER NOT NULL DEFAULT 0,
    author_id INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    published_at TEXT
);
"""


def get_connection(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def connect(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """`with db.connect() as conn:` — closes the connection even on error."""
    conn = get_connection(path)
    try:
        yield conn
    finally:
        conn.close()


def init_db(path: Path | None = None) -> None:
    conn = get_connection(path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
