"""
database/db.py
SQLite database connection and schema management for conversation memory,
chat sessions, and research reports metadata.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from config import settings
from logger import get_logger

logger = get_logger(__name__)

DB_PATH = settings.base_dir / Path(settings.SQLITE_DB_PATH)


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    title TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    chunk_count INTEGER NOT NULL,
    uploaded_at TEXT NOT NULL,
    session_id TEXT
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    query TEXT NOT NULL,
    file_path TEXT NOT NULL,
    confidence_score REAL,
    hallucination_score REAL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages (session_id);
CREATE INDEX IF NOT EXISTS idx_reports_session ON reports (session_id);
"""


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """
    Context manager that yields a SQLite connection with row factory set,
    and commits/closes automatically.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Database transaction failed; rolled back.")
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialize the SQLite database with the required schema."""
    try:
        with get_connection() as conn:
            conn.executescript(SCHEMA)
        logger.info("Database initialized at %s", DB_PATH)
    except Exception:
        logger.exception("Failed to initialize database.")
        raise


if __name__ == "__main__":
    init_db()
