"""Gamification milestone evaluation.

7 milestones tied to real acoustic progress. Each is earned once only.
The set of earned milestone IDs is stored as JSON in sessions.milestone_flags_json.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class MilestoneID(str, Enum):
    """Stable string IDs for persistence — do not rename without a migration."""
    FIRST_TEN_MINUTES = "first_ten_minutes"
    F0_FLOOR_LIFTER = "f0_floor_lifter"
    FEMININE_FREQUENCY = "feminine_frequency"
    INTONATION_EXPLORER = "intonation_explorer"
    VOWEL_SPACE_SHIFT = "vowel_space_shift"
    WEEK_WARRIOR = "week_warrior"
    MONTH_STRONG = "month_strong"


@dataclass
class SessionStats:
    """Statistics computed from the just-completed session."""
    avg_f0: float
    f0_std_dev: float
    avg_f2: float
    duration_secs: float


@dataclass
class HistoryStats:
    """Aggregated statistics from the user's history, including this session."""
    total_sessions: int
    streak: int
    total_practice_secs: float       # cumulative sum of all session durations
    f2_above_baseline_streak: int    # consecutive sessions where mean F2 > 120% of baseline
    f0_above_165_sessions: int       # cumulative sessions with avg_f0 > 165 Hz
    f0_above_185_sessions: int       # cumulative sessions with avg_f0 > 185 Hz
    baseline_f2: float
    already_earned: frozenset[str] = field(default_factory=frozenset)


_F2_SHIFT_THRESHOLD = 1.20   # 20% above baseline
_F0_STD_DEV_THRESHOLD = 30.0  # Hz — intonation marker


def evaluate_milestones(session: SessionStats, history: HistoryStats) -> set[MilestoneID]:
    """Return the set of milestones newly earned this session.

    Does not mutate the history. The caller is responsible for persisting
    newly earned milestones to the database.

    Args:
        session: Stats from the session just completed.
        history: Cumulative history including the current session's contribution.

    Returns:
        Set of MilestoneID values earned for the first time this session.
    """
    newly_earned: set[MilestoneID] = set()

    def _check(mid: MilestoneID, condition: bool) -> None:
        if condition and mid.value not in history.already_earned:
            newly_earned.add(mid)

    _check(MilestoneID.FIRST_TEN_MINUTES, history.total_practice_secs >= 600)
    # F0 Floor Lifter fires the FIRST time avg_f0 exceeds 165 Hz.
    # "First time" is enforced by the already_earned guard in _check():
    # if MilestoneID.F0_FLOOR_LIFTER is already in history.already_earned,
    # _check() is a no-op and the milestone is NOT re-awarded.
    _check(MilestoneID.F0_FLOOR_LIFTER, session.avg_f0 > 165.0)
    cumulative_f0_above_185 = history.f0_above_185_sessions + (1 if session.avg_f0 > 185.0 else 0)
    _check(MilestoneID.FEMININE_FREQUENCY, cumulative_f0_above_185 >= 3)
    _check(MilestoneID.INTONATION_EXPLORER, session.f0_std_dev > _F0_STD_DEV_THRESHOLD)
    _check(
        MilestoneID.VOWEL_SPACE_SHIFT,
        history.f2_above_baseline_streak >= 3
        and history.baseline_f2 > 0
        and session.avg_f2 > history.baseline_f2 * _F2_SHIFT_THRESHOLD,
    )
    _check(MilestoneID.WEEK_WARRIOR, history.streak >= 7)
    _check(MilestoneID.MONTH_STRONG, history.streak >= 30)

    return newly_earned
