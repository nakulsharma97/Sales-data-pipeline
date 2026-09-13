"""
Central configuration: loads environment variables and builds the MySQL URI.

All credentials come from environment variables (or a local .env file).
Never hardcode passwords anywhere in the code.
"""

import os
from urllib.parse import quote

try:
    from dotenv import load_dotenv

    # Load .env if present (local development convenience).
    load_dotenv()
except ImportError:  # python-dotenv is optional; env vars still work without it
    pass


def build_mysql_uri(
    user: str | None = None,
    password: str | None = None,
    host: str | None = None,
    port: str | None = None,
    database: str | None = None,
) -> str:
    """
    Build a MySQL connection URI from environment variables.

    Reads MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE.
    If MYSQL_URI is set, it is returned as-is.
    Password is URL-encoded so special characters are safe.
    """
    uri = os.environ.get("MYSQL_URI")
    if uri:
        return uri

    user = user or os.environ.get("MYSQL_USER")
    password = password or os.environ.get("MYSQL_PASSWORD")
    host = host or os.environ.get("MYSQL_HOST", "localhost")
    port = port or os.environ.get("MYSQL_PORT", "3306")
    database = database or os.environ.get("MYSQL_DATABASE")

    missing = [
        name
        for name, value in [
            ("MYSQL_USER", user),
            ("MYSQL_PASSWORD", password),
            ("MYSQL_DATABASE", database),
        ]
        if not value
    ]
    if missing:
        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill in your credentials."
        )

    return (
        f"mysql+pymysql://{quote(user)}:{quote(password)}"
        f"@{host}:{port}/{database}"
    )
