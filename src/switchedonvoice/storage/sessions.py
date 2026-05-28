"""Session CRUD, streak calculation, and aggregate stats."""
from __future__ import annotations
import math
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any
import json

from switchedonvoice.storage.db import get_connection


def _validate_session_stats(
    duration_secs: float,
    avg_f0: float,
    f0_std_dev: float,
    avg_f2: float,
) -> None:
    """Raise ValueError for non-finite or negative session statistics."""
    for name, val in [
        ("duration_secs", duration_secs),
        ("avg_f0", avg_f0),
        ("f0_std_dev", f0_std_dev),
        ("avg_f2", avg_f2),
    ]:
        if not math.isfinite(val):
            raise ValueError(f"{name} must be finite, got {val!r}")
        if val < 0:
            raise ValueError(f"{name} must be non-negative, got {val!r}")


def create_session(db_path: Path) -> int:
    """Insert a new session row and return its ID."""
    con = get_connection(db_path)
    cur = con.execute(
        "INSERT INTO sessions (date) VALUES (?)",
        (date.today().isoformat(),),
    )
    session_id = cur.lastrowid
    con.commit()
    con.close()
    assert session_id is not None
    return session_id


def close_session(
    db_path: Path,
    session_id: int,
    duration_secs: float,
    avg_f0: float,
    f0_std_dev: float,
    avg_f2: float,
    milestone_flags: dict[str, bool],
    date_override: str | None = None,
) -> None:
    """Update session summary statistics on close."""
    _validate_session_stats(duration_secs, avg_f0, f0_std_dev, avg_f2)
    con = get_connection(db_path)
    row_date = date_override or date.today().isoformat()
    cur = con.execute(
        """UPDATE sessions
           SET date=?, duration_secs=?, avg_f0=?, f0_std_dev=?, avg_f2=?, milestone_flags_json=?
           WHERE id=?""",
        (row_date, duration_secs, avg_f0, f0_std_dev, avg_f2,
         json.dumps(milestone_flags), session_id),
    )
    if cur.rowcount == 0:
        con.close()
        raise ValueError(f"Session {session_id} does not exist")
    con.commit()
    con.close()


def update_session_milestones(db_path: Path, session_id: int, flags: dict[str, bool]) -> None:
    """Patch the milestone_flags_json on a session that has already been closed."""
    con = get_connection(db_path)
    cur = con.execute(
        "UPDATE sessions SET milestone_flags_json=? WHERE id=?",
        (json.dumps(flags), session_id),
    )
    if cur.rowcount == 0:
        con.close()
        raise ValueError(f"Session {session_id} does not exist")
    con.commit()
    con.close()


def add_frame(
    db_path: Path,
    session_id: int,
    timestamp_ms: int,
    f0: float | None,
    f1: float | None,
    f2: float | None,
    cpp: float | None,
) -> None:
    """Insert a single decimated frame row."""
    con = get_connection(db_path)
    con.execute(
        "INSERT INTO frames (session_id, timestamp_ms, f0, f1, f2, cpp) VALUES (?,?,?,?,?,?)",
        (session_id, timestamp_ms, f0, f1, f2, cpp),
    )
    con.commit()
    con.close()


def get_all_sessions(db_path: Path) -> list[dict[str, Any]]:
    """Return all session rows as dicts, newest first."""
    con = get_connection(db_path)
    cur = con.execute("SELECT * FROM sessions ORDER BY id DESC")
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    con.close()
    return rows


def get_streak(db_path: Path) -> int:
    """Return current consecutive day streak ending today."""
    con = get_connection(db_path)
    cur = con.execute(
        "SELECT DISTINCT date FROM sessions WHERE date IS NOT NULL ORDER BY date DESC"
    )
    dates = [row[0] for row in cur.fetchall()]
    con.close()

    if not dates:
        return 0

    streak = 0
    check = date.today()
    for d_str in dates:
        d = date.fromisoformat(d_str)
        if d == check:
            streak += 1
            check -= timedelta(days=1)
        elif d < check:
            break
    return streak


@dataclass
class HistoryAggregates:
    """Aggregated counts needed for milestone evaluation."""
    total_practice_secs: float
    streak: int
    f0_above_165_sessions: int
    f0_above_185_sessions: int
    f2_above_baseline_streak: int


def get_history_stats(db_path: Path, baseline_f2: float) -> HistoryAggregates:
    """Query aggregate session stats needed for milestone evaluation."""
    con = get_connection(db_path)

    row = con.execute(
        "SELECT COALESCE(SUM(duration_secs), 0.0) FROM sessions WHERE duration_secs IS NOT NULL"
    ).fetchone()
    total_practice_secs = float(row[0])

    f0_above_165 = int(con.execute(
        "SELECT COUNT(*) FROM sessions WHERE avg_f0 > 165.0"
    ).fetchone()[0])

    f0_above_185 = int(con.execute(
        "SELECT COUNT(*) FROM sessions WHERE avg_f0 > 185.0"
    ).fetchone()[0])

    threshold = baseline_f2 * 1.20 if baseline_f2 > 0 else float("inf")
    rows = con.execute(
        "SELECT avg_f2 FROM sessions WHERE avg_f2 IS NOT NULL ORDER BY id DESC"
    ).fetchall()
    f2_streak = 0
    for (avg_f2,) in rows:
        if avg_f2 is not None and avg_f2 > threshold:
            f2_streak += 1
        else:
            break

    con.close()
    current_streak = get_streak(db_path)
    return HistoryAggregates(
        total_practice_secs=total_practice_secs,
        streak=current_streak,
        f0_above_165_sessions=f0_above_165,
        f0_above_185_sessions=f0_above_185,
        f2_above_baseline_streak=f2_streak,
    )
