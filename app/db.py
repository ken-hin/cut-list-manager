"""Database connection handling.

One SQLite connection is opened per web request and closed when the request
ends. Foreign keys are turned on for every connection, since SQLite only
enforces them when asked to.
"""
import os
import sqlite3
from pathlib import Path

from flask import current_app, g

# The app folder sits inside the project folder, next to schema.sql,
# insert_data.sql and the database file that run_queries.sh creates.
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(PROJECT_DIR, "xmas_orders.db")

SETUP_HINT = "Run  flask --app app init-db  from the app folder to create it."


class DatabaseMissingError(Exception):
    """The database file doesn't exist or hasn't been loaded with schema.sql."""


def open_existing_db(db_path):
    """Open the database without creating it.

    A plain sqlite3.connect() silently creates an empty file when the path is
    wrong, and every page then fails with "no such table". Opening in
    read-write mode (not "rwc") makes a missing file an error instead.
    """
    uri = Path(db_path).resolve().as_uri() + "?mode=rw"
    try:
        connection = sqlite3.connect(uri, uri=True)
    except sqlite3.OperationalError:
        raise DatabaseMissingError(f"No database found at {db_path}. {SETUP_HINT}")

    has_tables = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'customer_order'"
    ).fetchone()
    if has_tables is None:
        connection.close()
        raise DatabaseMissingError(f"The database at {db_path} is empty. {SETUP_HINT}")
    return connection


def get_db():
    """Return this request's database connection, opening it if needed."""
    if "db" not in g:
        g.db = open_existing_db(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row  # rows can be read by column name
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    """Close the connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(db_path):
    """Create a fresh database from schema.sql and insert_data.sql."""
    if os.path.exists(db_path):
        os.remove(db_path)
    connection = sqlite3.connect(db_path)
    try:
        for file_name in ("schema.sql", "insert_data.sql"):
            with open(os.path.join(PROJECT_DIR, file_name)) as sql_file:
                connection.executescript(sql_file.read())
        connection.commit()
    finally:
        connection.close()
