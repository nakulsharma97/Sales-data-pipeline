"""
Authentication: signup, login and session handling.

- Users are stored in the MySQL `users` table (created on first use).
- Passwords are hashed with bcrypt; plain text is never stored.
- Streamlit session state tracks the logged-in user (`st.session_state.user`).
"""

from __future__ import annotations

import re
from datetime import datetime

import bcrypt
import pandas as pd
import streamlit as st
from sqlalchemy import text

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LEN = 6

USERS_DDL_MYSQL = """
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(120) NULL,
    hashed_password CHAR(60) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

USERS_DDL_SQLITE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    hashed_password TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


# ------------------------------------------------------------ validation
def validate_signup(email: str, password: str, confirm: str, full_name: str = ""):
    """Return an error message for invalid signup input, or None if valid."""
    if not full_name or not full_name.strip():
        return "Please enter your full name."
    if len(full_name.strip()) > 120:
        return "Full name is too long (maximum 120 characters)."
    if not email or not password or not confirm:
        return "All fields are required."
    if not EMAIL_RE.match(email):
        return "Please enter a valid email address (e.g. name@example.com)."
    if len(password) < MIN_PASSWORD_LEN:
        return f"Password must be at least {MIN_PASSWORD_LEN} characters long."
    if password != confirm:
        return "Passwords do not match."
    return None


def validate_login(email: str, password: str):
    """Return an error message for invalid login input, or None if valid."""
    if not email or not password:
        return "Email and password are required."
    if not EMAIL_RE.match(email):
        return "Please enter a valid email address."
    return None


# --------------------------------------------------------------- hashing
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


# -------------------------------------------------------------- database
def _users_engine():
    """Engine for the users table; created lazily so imports stay cheap."""
    from database.connection import get_mysql_engine

    return get_mysql_engine()


def _ensure_users_table(engine) -> None:
    ddl = USERS_DDL_SQLITE if engine.dialect.name == "sqlite" else USERS_DDL_MYSQL
    with engine.begin() as conn:
        conn.execute(text(ddl))
        # Migration: tables created before full_name existed get the column
        # added in place — existing users and passwords are untouched.
        if engine.dialect.name == "sqlite":
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(users)"))]
        else:
            cols = [
                row[0]
                for row in conn.execute(
                    text(
                        "SELECT COLUMN_NAME FROM information_schema.columns "
                        "WHERE table_schema = DATABASE() AND table_name = 'users'"
                    )
                )
            ]
        if "full_name" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(120) NULL"))


def email_exists(engine, email: str) -> bool:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT 1 FROM users WHERE email = :email"),
            {"email": email},
        ).first()
    return row is not None


def create_user(engine, email: str, password: str, full_name: str = "") -> int:
    """Insert a new user with a bcrypt-hashed password. Returns the user id."""
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO users (email, full_name, hashed_password) "
                "VALUES (:email, :full_name, :hashed_password)"
            ),
            {
                "email": email,
                "full_name": full_name.strip() or None,
                "hashed_password": hash_password(password),
            },
        )
    return int(result.lastrowid)


def get_user_by_email(engine, email: str):
    """Return (id, email, hashed_password, full_name) or None."""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT id, email, hashed_password, full_name FROM users "
                "WHERE email = :email"
            ),
            {"email": email},
        ).first()
    return tuple(row) if row else None


def get_user_by_id(engine, user_id: int):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, email, created_at FROM users WHERE id = :id"),
            {"id": user_id},
        ).first()
    return tuple(row) if row else None


# -------------------------------------------------------- streamlit flows
def signup_user(
    email: str, password: str, confirm: str, full_name: str = ""
) -> str | None:
    """
    Full signup flow with input validation and duplicate-email rejection.
    Returns an error message, or None on success (user is logged in).
    """
    error = validate_signup(email, password, confirm, full_name)
    if error:
        return error

    engine = _users_engine()
    _ensure_users_table(engine)
    if email_exists(engine, email):
        return "An account with this email already exists. Please log in instead."

    user_id = create_user(engine, email, password, full_name)
    st.session_state.user = {
        "id": user_id,
        "email": email,
        "full_name": full_name.strip(),
    }
    return None


def login_user(email: str, password: str) -> str | None:
    """
    Full login flow. Returns an error message, or None on success
    (st.session_state.user is set).
    """
    error = validate_login(email, password)
    if error:
        return error

    engine = _users_engine()
    _ensure_users_table(engine)
    user = get_user_by_email(engine, email)
    if user is None or not verify_password(password, user[2]):
        return "Invalid email or password."

    st.session_state.user = {
        "id": user[0],
        "email": user[1],
        "full_name": (user[3] or "").strip(),
    }
    return None


def logout() -> None:
    for key in ("user", "df_source", "uploaded_df", "auth_mode"):
        st.session_state.pop(key, None)


def current_user() -> dict | None:
    return st.session_state.get("user")


def display_name(user: dict | None) -> str:
    """Best display name for the navbar: registered name, else email prefix."""
    if not user:
        return "Guest"
    name = (user.get("full_name") or "").strip()
    if name:
        return name
    email = user.get("email", "")
    return email.split("@")[0].replace(".", " ").title() if email else "Guest"
