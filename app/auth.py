"""Password hashing, session cookies, and the require_login dependency.

Session cookie holds a signed user id (itsdangerous) — never anything secret
in the clear, and the signature means a client can't forge or tamper with it.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, Request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app import db, settings

SESSION_COOKIE = "session"
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt="session")


def session_cookie_value(user_id: int) -> str:
    return _serializer().dumps({"user_id": user_id})


def _user_id_from_cookie(raw: str | None) -> int | None:
    if not raw:
        return None
    try:
        data = _serializer().loads(raw, max_age=60 * 60 * 24 * 7)
    except BadSignature:
        return None
    return data.get("user_id")


@dataclass
class User:
    id: int
    email: str
    role: str
    active: bool


def _row_to_user(row: sqlite3.Row) -> User:
    return User(id=row["id"], email=row["email"], role=row["role"], active=bool(row["active"]))


def get_current_user(request: Request) -> User | None:
    user_id = _user_id_from_cookie(request.cookies.get(SESSION_COOKIE))
    if user_id is None:
        return None
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None or not row["active"]:
        return None
    return _row_to_user(row)


def require_login(request: Request) -> User:
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user
