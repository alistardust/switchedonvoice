"""SQLite schema initialisation and connection management.

Schema:
  sessions(id, date, duration_secs, avg_f0, f0_std_dev, avg_f2, milestone_flags_json)
  frames(session_id, timestamp_ms, f0, f1, f2, cpp)

Frames are stored at 5–10 Hz (decimated by the caller). A 60-min session
generates approximately 18,000 rows.
"""
import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    date             TEXT NOT NULL,
    duration_secs    REAL,
    avg_f0           REAL,
    f0_std_dev       REAL,
    avg_f2           REAL,
    milestone_flags_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS frames (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES sessions(id),
    timestamp_ms INTEGER NOT NULL,
    f0          REAL,
    f1          REAL,
    f2          REAL,
    cpp         REAL
);

CREATE INDEX IF NOT EXISTS idx_frames_session ON frames(session_id);
"""

_CURRENT_SCHEMA_VERSION = 1


def _migrate(con: sqlite3.Connection) -> None:
    """Run schema migrations in version order.

    Each block is idempotent. To add a migration:
      1. Add an ``elif version < N`` block here.
      2. Bump ``_CURRENT_SCHEMA_VERSION`` above.
    Never remove or reorder existing migration blocks.
    """
    version: int = con.execute("PRAGMA user_version").fetchone()[0]
    if version < 1:
        con.execute(f"PRAGMA user_version = {_CURRENT_SCHEMA_VERSION}")


def init_db(db_path: Path) -> None:
    """Create tables and run any pending schema migrations.

    Args:
        db_path: Path to the SQLite database file. Created if absent.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(_SCHEMA)
    _migrate(con)
    con.commit()
    con.close()


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Return an open connection with WAL mode and foreign keys enabled.

    The caller is responsible for closing the connection.

    Args:
        db_path: Path to an initialised SQLite database.

    Returns:
        Open sqlite3.Connection.
    """
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con
