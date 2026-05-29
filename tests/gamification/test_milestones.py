# tests/gamification/test_milestones.py
"""Tests for gamification milestone evaluation."""
import pytest
from switchedonvoice.gamification.milestones import (
    MilestoneID,
    evaluate_milestones,
    SessionStats,
    HistoryStats,
)


def make_session(avg_f0: float = 180.0, f0_std_dev: float = 25.0,
                 avg_f2: float = 1700.0, duration_secs: float = 600.0) -> SessionStats:
    return SessionStats(avg_f0=avg_f0, f0_std_dev=f0_std_dev,
                        avg_f2=avg_f2, duration_secs=duration_secs)


def make_history(total_sessions: int = 1, streak: int = 1,
                 f2_above_baseline_streak: int = 0,
                 f0_above_165_sessions: int = 0,
                 f0_above_185_sessions: int = 0,
                 baseline_f2: float = 1400.0,
                 total_practice_secs: float = 0.0,
                 already_earned: set[str] | None = None) -> HistoryStats:
    return HistoryStats(
        total_sessions=total_sessions,
        streak=streak,
        f2_above_baseline_streak=f2_above_baseline_streak,
        f0_above_165_sessions=f0_above_165_sessions,
        f0_above_185_sessions=f0_above_185_sessions,
        baseline_f2=baseline_f2,
        total_practice_secs=total_practice_secs,
        already_earned=frozenset(already_earned) if already_earned else frozenset(),
    )


def test_first_10_minutes_requires_cumulative_600s() -> None:
    # 400s in history + 300s this session = 700s total → earns it
    earned = evaluate_milestones(
        make_session(duration_secs=300.0),
        make_history(total_practice_secs=700.0),
    )
    assert MilestoneID.FIRST_TEN_MINUTES in earned


def test_first_10_minutes_not_earned_if_cumulative_under_600s() -> None:
    earned = evaluate_milestones(
        make_session(duration_secs=300.0),
        make_history(total_practice_secs=500.0),
    )
    assert MilestoneID.FIRST_TEN_MINUTES not in earned


def test_f0_floor_lifter_triggers_at_165hz() -> None:
    earned = evaluate_milestones(
        make_session(avg_f0=166.0),
        make_history(f0_above_165_sessions=0),
    )
    assert MilestoneID.F0_FLOOR_LIFTER in earned


def test_f0_floor_lifter_not_triggered_at_exactly_165hz() -> None:
    earned = evaluate_milestones(
        make_session(avg_f0=165.0),
        make_history(f0_above_165_sessions=0),
    )
    assert MilestoneID.F0_FLOOR_LIFTER not in earned


def test_feminine_frequency_requires_3_sessions() -> None:
    earned = evaluate_milestones(
        make_session(avg_f0=190.0),
        make_history(f0_above_185_sessions=2),
    )
    assert MilestoneID.FEMININE_FREQUENCY in earned

    earned2 = evaluate_milestones(
        make_session(avg_f0=190.0),
        make_history(f0_above_185_sessions=1),
    )
    assert MilestoneID.FEMININE_FREQUENCY not in earned2


def test_intonation_explorer_requires_std_dev_above_30hz() -> None:
    earned_yes = evaluate_milestones(
        make_session(f0_std_dev=31.0),
        make_history(),
    )
    earned_no = evaluate_milestones(
        make_session(f0_std_dev=29.9),
        make_history(),
    )
    assert MilestoneID.INTONATION_EXPLORER in earned_yes
    assert MilestoneID.INTONATION_EXPLORER not in earned_no


def test_intonation_explorer_exact_boundary_30hz() -> None:
    """30.0 Hz is the boundary — strictly greater-than, so 30.0 must NOT earn."""
    earned = evaluate_milestones(make_session(f0_std_dev=30.0), make_history())
    assert MilestoneID.INTONATION_EXPLORER not in earned


def test_vowel_space_shift_requires_3_consecutive_sessions() -> None:
    # F2 = 1400 baseline → threshold = 1680. Streak of 3 with current avg_f2 > 1680 → earns
    earned_yes = evaluate_milestones(
        make_session(avg_f2=1700.0),
        make_history(f2_above_baseline_streak=3, baseline_f2=1400.0),
    )
    earned_no = evaluate_milestones(
        make_session(avg_f2=1700.0),
        make_history(f2_above_baseline_streak=2, baseline_f2=1400.0),
    )
    assert MilestoneID.VOWEL_SPACE_SHIFT in earned_yes
    assert MilestoneID.VOWEL_SPACE_SHIFT not in earned_no


def test_vowel_space_shift_exact_threshold() -> None:
    """avg_f2 exactly at baseline_f2 * 1.20 must NOT earn (strictly greater-than)."""
    baseline_f2 = 1400.0
    exact_threshold_f2 = baseline_f2 * 1.20  # 1680.0
    earned = evaluate_milestones(
        make_session(avg_f2=exact_threshold_f2),
        make_history(f2_above_baseline_streak=3, baseline_f2=baseline_f2),
    )
    assert MilestoneID.VOWEL_SPACE_SHIFT not in earned


def test_week_warrior_requires_7_day_streak() -> None:
    earned_7 = evaluate_milestones(make_session(), make_history(streak=7))
    earned_6 = evaluate_milestones(make_session(), make_history(streak=6))
    assert MilestoneID.WEEK_WARRIOR in earned_7
    assert MilestoneID.WEEK_WARRIOR not in earned_6


def test_month_strong_requires_30_day_streak() -> None:
    earned_30 = evaluate_milestones(make_session(), make_history(streak=30))
    earned_29 = evaluate_milestones(make_session(), make_history(streak=29))
    assert MilestoneID.MONTH_STRONG in earned_30
    assert MilestoneID.MONTH_STRONG not in earned_29


def test_already_earned_milestones_not_re_awarded() -> None:
    earned = evaluate_milestones(
        make_session(duration_secs=700, f0_std_dev=35.0),
        make_history(total_practice_secs=700.0, already_earned={
            MilestoneID.FIRST_TEN_MINUTES.value,
            MilestoneID.INTONATION_EXPLORER.value,
        }),
    )
    assert MilestoneID.FIRST_TEN_MINUTES not in earned
    assert MilestoneID.INTONATION_EXPLORER not in earned


def test_f0_floor_lifter_not_re_awarded_when_already_earned() -> None:
    """Earning F0 Floor Lifter once should never award it again, even if F0 stays high."""
    earned_first = evaluate_milestones(
        make_session(avg_f0=166.0),
        make_history(already_earned=set()),
    )
    assert MilestoneID.F0_FLOOR_LIFTER in earned_first

    earned_second = evaluate_milestones(
        make_session(avg_f0=200.0),
        make_history(already_earned={MilestoneID.F0_FLOOR_LIFTER.value}),
    )
    assert MilestoneID.F0_FLOOR_LIFTER not in earned_second


def test_vowel_space_shift_not_earned_when_baseline_f2_is_zero() -> None:
    """Even with streak >= 3, cannot earn if baseline_f2 = 0."""
    earned = evaluate_milestones(
        make_session(avg_f2=1700.0),
        make_history(f2_above_baseline_streak=3, baseline_f2=0.0),
    )
    assert MilestoneID.VOWEL_SPACE_SHIFT not in earned


def test_first_10_minutes_exact_600s_boundary() -> None:
    """Exactly 600.0 seconds must earn (>= 600, not > 600)."""
    earned = evaluate_milestones(
        make_session(duration_secs=100.0),
        make_history(total_practice_secs=600.0),
    )
    assert MilestoneID.FIRST_TEN_MINUTES in earned


def test_feminine_frequency_earned_without_current_session_contributing() -> None:
    """Can earn with 3+ historical sessions, even if current session is below 185 Hz."""
    earned = evaluate_milestones(
        make_session(avg_f0=180.0),
        make_history(f0_above_185_sessions=3),
    )
    assert MilestoneID.FEMININE_FREQUENCY in earned
