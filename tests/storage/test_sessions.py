# tests/storage/test_sessions.py
"""Tests for session CRUD and streak calculation."""
import json
from datetime import date, timedelta
from pathlib import Path
import pytest
from switchedonvoice.storage.db import init_db
from switchedonvoice.storage.sessions import (
    HistoryAggregates,
    create_session,
    close_session,
    add_frame,
    get_streak,
    get_all_sessions,
    get_history_stats,
)


@pytest.fixture()
def db(tmp_path: Path) -> Path:
    p = tmp_path / "test.db"
    init_db(p)
    return p


def test_create_and_close_session(db: Path) -> None:
    session_id = create_session(db)
    assert isinstance(session_id, int)
    close_session(db, session_id, duration_secs=300.0, avg_f0=185.0,
                  f0_std_dev=25.0, avg_f2=1800.0, milestone_flags={})
    import sqlite3 as _sqlite3
    con = _sqlite3.connect(db)
    row = con.execute(
        "SELECT duration_secs, avg_f0, f0_std_dev, avg_f2, milestone_flags_json "
        "FROM sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    con.close()
    assert row is not None
    assert row[0] == pytest.approx(300.0)
    assert row[1] == pytest.approx(185.0)
    assert row[2] == pytest.approx(25.0)
    assert row[3] == pytest.approx(1800.0)
    assert json.loads(row[4]) == {}


def test_add_frame(db: Path) -> None:
    session_id = create_session(db)
    add_frame(db, session_id, timestamp_ms=1000, f0=185.0, f1=500.0, f2=1800.0, cpp=12.0)


def test_get_all_sessions(db: Path) -> None:
    sid = create_session(db)
    close_session(db, sid, 60.0, 180.0, 20.0, 1700.0, {})
    sessions = get_all_sessions(db)
    assert len(sessions) == 1


def test_streak_empty_db(db: Path) -> None:
    assert get_streak(db) == 0


def test_streak_consecutive_days(db: Path) -> None:
    today = date.today()
    for i in range(3):
        d = (today - timedelta(days=i)).isoformat()
        sid = create_session(db)
        close_session(db, sid, 60.0, 180.0, 20.0, 1700.0, {}, date_override=d)
    assert get_streak(db) == 3


def test_streak_broken(db: Path) -> None:
    today = date.today()
    for i in [0, 2]:  # gap on day 1
        d = (today - timedelta(days=i)).isoformat()
        sid = create_session(db)
        close_session(db, sid, 60.0, 180.0, 20.0, 1700.0, {}, date_override=d)
    assert get_streak(db) == 1


def test_streak_multiple_sessions_same_day_count_once(db: Path) -> None:
    today = date.today().isoformat()
    for _ in range(3):
        sid = create_session(db)
        close_session(db, sid, 60.0, 180.0, 20.0, 1700.0, {}, date_override=today)
    assert get_streak(db) == 1


def test_streak_no_session_today_is_zero(db: Path) -> None:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    sid = create_session(db)
    close_session(db, sid, 60.0, 180.0, 20.0, 1700.0, {}, date_override=yesterday)
    assert get_streak(db) == 0


def test_get_history_stats_empty_db(db: Path) -> None:
    stats = get_history_stats(db, baseline_f2=1600.0)
    assert isinstance(stats, HistoryAggregates)
    assert stats.total_practice_secs == 0
    assert stats.f0_above_165_sessions == 0
    assert stats.f0_above_185_sessions == 0
    assert stats.streak == 0
    assert stats.f2_above_baseline_streak == 0


def test_get_history_stats_totals(db: Path) -> None:
    for _ in range(3):
        sid = create_session(db)
        close_session(db, sid, duration_secs=600.0, avg_f0=190.0,
                      f0_std_dev=20.0, avg_f2=1950.0, milestone_flags={})
    stats = get_history_stats(db, baseline_f2=1600.0)
    assert stats.total_practice_secs == pytest.approx(1800.0)
    assert stats.f0_above_165_sessions == 3
    assert stats.f0_above_185_sessions == 3


def test_get_history_stats_f0_boundaries(db: Path) -> None:
    """avg_f0 == 165 should NOT count as above 165 (strict greater-than)."""
    sid = create_session(db)
    close_session(db, sid, 60.0, avg_f0=165.0, f0_std_dev=0.0, avg_f2=1700.0,
                  milestone_flags={})
    stats = get_history_stats(db, baseline_f2=1600.0)
    assert stats.f0_above_165_sessions == 0

    sid2 = create_session(db)
    close_session(db, sid2, 60.0, avg_f0=165.1, f0_std_dev=0.0, avg_f2=1700.0,
                  milestone_flags={})
    stats2 = get_history_stats(db, baseline_f2=1600.0)
    assert stats2.f0_above_165_sessions == 1


def test_get_history_stats_f2_streak(db: Path) -> None:
    """Sessions with avg_f2 > baseline * 1.20 contribute to f2_above_baseline_streak."""
    baseline_f2 = 1600.0
    threshold = baseline_f2 * 1.20  # 1920.0
    today = date.today()
    for i in range(3):
        d = (today - timedelta(days=2 - i)).isoformat()
        sid = create_session(db)
        close_session(db, sid, 60.0, 185.0, 20.0, avg_f2=threshold + 1.0,
                      milestone_flags={}, date_override=d)
    stats = get_history_stats(db, baseline_f2=baseline_f2)
    assert stats.f2_above_baseline_streak >= 3


def test_get_history_stats_streak_is_non_zero_when_session_today(db: Path) -> None:
    sid = create_session(db)
    close_session(db, sid, 60.0, avg_f0=190.0, f0_std_dev=20.0,
                  avg_f2=1900.0, milestone_flags={})
    stats = get_history_stats(db, baseline_f2=1600.0)
    assert stats.streak >= 1
