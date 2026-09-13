"""
Tests for configuration and database connection handling.

These never need a real MySQL server: they check that URIs are built
correctly from environment variables and that failures raise clear,
friendly errors.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import get_mysql_engine  # noqa: E402
from utils.config import build_mysql_uri  # noqa: E402

DB_ENV_VARS = [
    "MYSQL_URI",
    "MYSQL_USER",
    "MYSQL_PASSWORD",
    "MYSQL_HOST",
    "MYSQL_PORT",
    "MYSQL_DATABASE",
    "MYSQL_ROOT_PASSWORD",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Remove all MySQL env vars (including any loaded from .env)."""
    for var in DB_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_build_uri_from_parts():
    uri = build_mysql_uri(
        user="retail_user",
        password="p@ss word",
        host="localhost",
        port="3306",
        database="retail_demo",
    )
    assert uri == "mysql+pymysql://retail_user:p%40ss%20word@localhost:3306/retail_demo"


def test_build_uri_from_env(monkeypatch):
    monkeypatch.setenv("MYSQL_USER", "u1")
    monkeypatch.setenv("MYSQL_PASSWORD", "pw")
    monkeypatch.setenv("MYSQL_DATABASE", "db1")
    assert build_mysql_uri() == "mysql+pymysql://u1:pw@localhost:3306/db1"


def test_full_uri_takes_precedence(monkeypatch):
    monkeypatch.setenv("MYSQL_URI", "mysql+pymysql://x:y@host:1/db")
    assert build_mysql_uri() == "mysql+pymysql://x:y@host:1/db"


def test_missing_vars_raise_helpful_error():
    with pytest.raises(ValueError) as excinfo:
        build_mysql_uri()
    message = str(excinfo.value)
    assert "MYSQL_USER" in message
    assert ".env" in message  # points the user to the fix


def test_get_mysql_engine_missing_config_raises_connection_error():
    """No credentials -> friendly ConnectionError, not a raw ValueError."""
    with pytest.raises(ConnectionError) as excinfo:
        get_mysql_engine()
    assert "Missing required environment variables" in str(excinfo.value)


def test_get_mysql_engine_unreachable_server():
    """Bad credentials/host -> clear ConnectionError (fails fast, 1s timeout)."""
    bad_uri = "mysql+pymysql://baduser:badpass@127.0.0.1:59999/bad?connect_timeout=1"
    with pytest.raises(ConnectionError) as excinfo:
        get_mysql_engine(bad_uri)
    assert "Could not connect to MySQL" in str(excinfo.value)
