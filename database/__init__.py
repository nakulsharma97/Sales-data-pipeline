"""
Database connection helpers.

Credentials come from environment variables (see utils/config.py).
Connection failures raise a clear ConnectionError so the dashboard can
show a friendly setup message instead of a stack trace.
"""

from database.connection import get_mysql_engine  # noqa: F401 (re-export)
