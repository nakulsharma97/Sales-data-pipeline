"""
Database connection helpers.

Credentials come from environment variables (see utils/config.py).
Connection failures raise a clear ConnectionError so the dashboard can
show a friendly setup message instead of a stack trace.
"""

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from utils.config import build_mysql_uri


def get_mysql_engine(mysql_uri: str | None = None):
    """
    Create and return a SQLAlchemy engine for MySQL.

    - Reads MYSQL_URI, or builds one from MYSQL_USER/PASSWORD/HOST/PORT/DATABASE
    - pool_pre_ping avoids stale connections on cloud databases
    - Raises ConnectionError with a readable message when the DB is unreachable
    """
    if not mysql_uri:
        try:
            mysql_uri = build_mysql_uri()
        except ValueError as exc:
            # Surface configuration problems the same way as connection problems
            raise ConnectionError(str(exc)) from exc

    try:
        engine = create_engine(mysql_uri, echo=False, pool_pre_ping=True)
        # Validate the connection immediately so failures surface here
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return engine
    except SQLAlchemyError as exc:
        reason = str(exc).split("\n")[0]
        raise ConnectionError(
            "Could not connect to MySQL. Check your .env credentials and that "
            f"the database server is running. Details: {reason}"
        ) from exc


def get_mysql_connection(mysql_uri: str | None = None):
    """Open and return a single MySQL connection."""
    engine = get_mysql_engine(mysql_uri)
    return engine.connect()
