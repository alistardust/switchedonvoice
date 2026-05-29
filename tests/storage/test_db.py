# tests/storage/test_db.py
"""Tests for SQLite schema initialisation and migration."""
import sqlite3
import tempfile
from pathlib import Path
import pytest
from switchedonvoice.storage.db import init_db, get_connection


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


def test_init_creates_sessions_table(db_path: Path) -> None:
    init_db(db_path)
    con = sqlite3.connect(db_path)
    cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
    assert cur.fetchone() is not None
    con.close()


def test_init_creates_frames_table(db_path: Path) -> None:
    init_db(db_path)
    con = sqlite3.connect(db_path)
    cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='frames'")
    assert cur.fetchone() is not None
    con.close()


def test_init_is_idempotent(db_path: Path) -> None:
    init_db(db_path)
    init_db(db_path)  # Second call must not raise


def test_get_connection_returns_connection(db_path: Path) -> None:
    init_db(db_path)
    con = get_connection(db_path)
    assert isinstance(con, sqlite3.Connection)
    con.close()


def test_sessions_table_has_expected_columns(db_path: Path) -> None:
    init_db(db_path)
    con = sqlite3.connect(db_path)
    cur = con.execute("PRAGMA table_info(sessions)")
    columns = {row[1] for row in cur.fetchall()}
    con.close()
    expected = {"id", "date", "duration_secs", "avg_f0", "f0_std_dev", "avg_f2", "milestone_flags_json"}
    assert expected.issubset(columns)


def test_frames_table_has_expected_columns(db_path: Path) -> None:
    init_db(db_path)
    con = sqlite3.connect(db_path)
    cur = con.execute("PRAGMA table_info(frames)")
    columns = {row[1] for row in cur.fetchall()}
    con.close()
    expected = {"id", "session_id", "timestamp_ms", "f0", "f1", "f2", "cpp"}
    assert expected.issubset(columns)


def test_schema_version_is_set(db_path: Path) -> None:
    init_db(db_path)
    con = sqlite3.connect(db_path)
    version = con.execute("PRAGMA user_version").fetchone()[0]
    con.close()
    assert version == 1  # bump this with each schema migration
