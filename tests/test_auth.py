"""
Tests for authentication: validation, bcrypt hashing, duplicate emails,
and the Streamlit session-state login/signup flows (run against SQLite).
"""

import os
import sys

import pandas as pd
import pytest
from sqlalchemy import create_engine

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import auth  # noqa: E402


@pytest.fixture(scope="module")
def engine(tmp_path_factory):
    """SQLite database with the users table, shared by this module."""
    eng = create_engine(f"sqlite:///{tmp_path_factory.mktemp('auth') / 'users.db'}")
    auth._ensure_users_table(eng)
    return eng


# ------------------------------------------------------- input validation
def test_validate_signup_rejects_missing_fields():
    assert auth.validate_signup("", "secret123", "secret123", "Nakul Sharma") is not None
    assert auth.validate_signup("a@b.com", "", "secret123", "Nakul Sharma") is not None
    assert auth.validate_signup("a@b.com", "secret123", "", "Nakul Sharma") is not None


def test_validate_signup_rejects_missing_name():
    message = auth.validate_signup("a@b.com", "secret123", "secret123", "")
    assert message is not None and "full name" in message.lower()
    assert auth.validate_signup("a@b.com", "secret123", "secret123", "   ") is not None


def test_validate_signup_rejects_bad_email():
    assert auth.validate_signup("not-an-email", "secret123", "secret123", "Nakul") is not None
    assert auth.validate_signup("a@b", "secret123", "secret123", "Nakul") is not None
    assert auth.validate_signup("a b@c.com", "secret123", "secret123", "Nakul") is not None


def test_validate_signup_rejects_short_password():
    message = auth.validate_signup("a@b.com", "abc", "abc", "Nakul")
    assert message is not None and "6" in message


def test_validate_signup_rejects_mismatched_confirm():
    assert auth.validate_signup("a@b.com", "secret123", "different", "Nakul") is not None


def test_validate_signup_accepts_valid_input():
    assert (
        auth.validate_signup("user@example.com", "secret123", "secret123", "Nakul Sharma")
        is None
    )


def test_validate_login_rejects_bad_email():
    assert auth.validate_login("nope", "pw123456") is not None


# ---------------------------------------------------------------- hashing
def test_hash_password_is_salted_and_not_plain():
    h1 = auth.hash_password("secret123")
    h2 = auth.hash_password("secret123")
    assert h1 != h2                      # salted: same password, different hashes
    assert "secret123" not in h1         # never stored in plain text
    assert h1.startswith("$2")           # bcrypt format
    assert len(h1) == 60


def test_verify_password_roundtrip():
    hashed = auth.hash_password("secret123")
    assert auth.verify_password("secret123", hashed) is True
    assert auth.verify_password("wrongpass", hashed) is False


def test_verify_password_handles_garbage_hash():
    assert auth.verify_password("x", "not-a-bcrypt-hash") is False


# ------------------------------------------------------- database + flows
def _fake_session_state():
    class FakeState(dict):
        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError:
                raise AttributeError(name)

        def __setattr__(self, name, value):
            self[name] = value

        def pop(self, name, default=None):
            return dict.pop(self, name, default)

    return FakeState()


@pytest.fixture()
def fake_st(monkeypatch):
    """Replace st.session_state with a plain dict-like object for tests."""
    state = _fake_session_state()
    monkeypatch.setattr(auth.st, "session_state", state)
    return state


def test_signup_then_login_flow(engine, fake_st, monkeypatch):
    monkeypatch.setattr(auth, "_users_engine", lambda: engine)

    assert (
        auth.signup_user("naya@example.com", "hunter22", "hunter22", "Naya Sharma")
        is None
    )
    assert fake_st["user"]["email"] == "naya@example.com"
    assert fake_st["user"]["full_name"] == "Naya Sharma"

    auth.logout()
    assert "user" not in fake_st

    assert auth.login_user("naya@example.com", "hunter22") is None
    assert fake_st["user"]["email"] == "naya@example.com"
    assert fake_st["user"]["full_name"] == "Naya Sharma"


def test_full_name_is_stored_in_database(engine, fake_st, monkeypatch):
    monkeypatch.setattr(auth, "_users_engine", lambda: engine)
    auth.signup_user("named@example.com", "hunter22", "hunter22", "Ravi Kumar")
    with engine.connect() as conn:
        row = conn.execute(
            auth.text("SELECT full_name FROM users WHERE email = :e"),
            {"e": "named@example.com"},
        ).first()
    assert row is not None and row[0] == "Ravi Kumar"


def test_duplicate_email_rejected(engine, fake_st, monkeypatch):
    monkeypatch.setattr(auth, "_users_engine", lambda: engine)
    error = auth.signup_user(
        "naya@example.com", "otherpass1", "otherpass1", "Someone Else"
    )
    assert error is not None and "already exists" in error


def test_login_wrong_password_rejected(engine, fake_st, monkeypatch):
    monkeypatch.setattr(auth, "_users_engine", lambda: engine)
    assert auth.login_user("naya@example.com", "wrongpass") is not None


def test_login_unknown_email_rejected(engine, fake_st, monkeypatch):
    monkeypatch.setattr(auth, "_users_engine", lambda: engine)
    assert auth.login_user("ghost@example.com", "whatever1") is not None


def test_stored_password_is_hashed(engine):
    with engine.connect() as conn:
        row = conn.execute(
            auth.text("SELECT hashed_password FROM users WHERE email = :e"),
            {"e": "naya@example.com"},
        ).first()
    assert row is not None
    stored = row[0]
    assert stored.startswith("$2") and len(stored) == 60


def test_current_user_reads_session(fake_st):
    fake_st["user"] = {"id": 1, "email": "x@y.com"}
    assert auth.current_user()["email"] == "x@y.com"


# --------------------------------------------------------- display name
def test_display_name_prefers_full_name():
    user = {"id": 1, "email": "n@example.com", "full_name": "Nakul Sharma"}
    assert auth.display_name(user) == "Nakul Sharma"


def test_display_name_falls_back_to_email_prefix():
    user = {"id": 1, "email": "nakul.sharma@example.com", "full_name": ""}
    assert auth.display_name(user) == "Nakul Sharma"


def test_display_name_guest_when_no_user():
    assert auth.display_name(None) == "Guest"
