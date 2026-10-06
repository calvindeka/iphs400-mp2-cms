"""T01: the CSRF double-submit-cookie primitive later tickets' forms use."""
from __future__ import annotations

from app import csrf


class FakeRequest:
    def __init__(self, cookies: dict[str, str]):
        self.cookies = cookies


class FakeResponse:
    def __init__(self):
        self.cookies_set: dict[str, str] = {}

    def set_cookie(self, name: str, value: str, **kwargs):
        self.cookies_set[name] = value


def test_get_or_create_token_makes_a_fresh_one_when_none_exists():
    token = csrf.get_or_create_token(FakeRequest({}))
    assert token


def test_get_or_create_token_reuses_an_existing_cookie():
    existing = "existing-token"
    assert csrf.get_or_create_token(FakeRequest({csrf.COOKIE_NAME: existing})) == existing


def test_apply_cookie_sets_it_when_request_had_none():
    response = FakeResponse()
    csrf.apply_cookie(FakeRequest({}), response, "new-token")
    assert response.cookies_set[csrf.COOKIE_NAME] == "new-token"


def test_apply_cookie_is_a_noop_when_request_already_had_the_same_token():
    response = FakeResponse()
    csrf.apply_cookie(FakeRequest({csrf.COOKIE_NAME: "abc"}), response, "abc")
    assert response.cookies_set == {}


def test_validate_accepts_matching_token():
    request = FakeRequest({csrf.COOKIE_NAME: "abc"})
    assert csrf.validate(request, "abc") is True


def test_validate_rejects_mismatched_or_missing_token():
    assert csrf.validate(FakeRequest({csrf.COOKIE_NAME: "abc"}), "xyz") is False
    assert csrf.validate(FakeRequest({}), "abc") is False
