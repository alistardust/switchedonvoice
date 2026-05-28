# src/switchedonvoice/ui/progress_panel.py
"""Progress panel: streak, milestone badges, weekly chart, and session history."""
from __future__ import annotations
import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPaintEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from switchedonvoice.gamification.milestones import MilestoneID
from switchedonvoice.storage.sessions import get_all_sessions, get_streak

_logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

_MILESTONE_NAMES: dict[str, str] = {
    MilestoneID.FIRST_TEN_MINUTES.value: "First Ten Minutes",
    MilestoneID.F0_FLOOR_LIFTER.value: "F0 Floor Lifter",
    MilestoneID.FEMININE_FREQUENCY.value: "Feminine Frequency",
    MilestoneID.INTONATION_EXPLORER.value: "Intonation Explorer",
    MilestoneID.VOWEL_SPACE_SHIFT.value: "Vowel Space Shift",
    MilestoneID.WEEK_WARRIOR.value: "Week Warrior",
    MilestoneID.MONTH_STRONG.value: "Month Strong",
}

_TABLE_COLUMNS = ("Date", "Duration (min)", "Avg F0 (Hz)", "F0 Std Dev (Hz)", "Avg F2 (Hz)")

_COLOR_EARNED = QColor(60, 180, 60)    # green
_COLOR_UNEARNED = QColor(100, 100, 100)  # grey
_COLOR_F0_LINE = QColor(60, 200, 100)   # green
_COLOR_STD_LINE = QColor(230, 200, 60)  # yellow
_COLOR_BG = QColor(20, 20, 30)
_COLOR_GRID = QColor(60, 60, 80)

_MAX_COORD: int = 10_000  # Qt coordinate safety bound
_WEEK_LABEL_STRIDE: int = 2  # Show every Nth x-axis label to avoid crowding


# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #


def _safe_int(val: float) -> int:
    """Clamp a float coordinate to safe Qt integer bounds.

    Prevents OverflowError when NaN or extreme values reach drawLine.

    Args:
        val: Float coordinate value.

    Returns:
        Clamped integer coordinate.
    """
    if not np.isfinite(val):
        return 0
    return max(-_MAX_COORD, min(_MAX_COORD, int(val)))


# --------------------------------------------------------------------------- #
# WeeklyChartWidget
# --------------------------------------------------------------------------- #


class WeeklyChartWidget(QWidget):
    """QPainter line chart: weekly mean F0 and F0 std dev per ISO calendar week."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._weeks: list[str] = []         # labels like "W23"
        self._f0_means: list[float] = []
        self._f0_stds: list[float] = []
        self.setMinimumSize(300, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(
        self,
        weeks: list[str],
        f0_means: list[float],
        f0_stds: list[float],
    ) -> None:
        """Load pre-aggregated weekly data and repaint.

        Note: Must be called from the GUI thread.

        Args:
            weeks: ISO week labels (e.g., ["W01", "W02"]).
            f0_means: Mean F0 per week (Hz).
            f0_stds: Mean F0 std dev per week (Hz).

        Raises:
            ValueError: If input lists have mismatched lengths.
        """
        if not (len(weeks) == len(f0_means) == len(f0_stds)):
            raise ValueError(
                f"Mismatched lengths: weeks={len(weeks)}, "
                f"f0_means={len(f0_means)}, f0_stds={len(f0_stds)}"
            )
        self._weeks = weeks
        self._f0_means = f0_means
        self._f0_stds = f0_stds
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:
        """Render the weekly chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, _COLOR_BG)

        n = len(self._weeks)
        if n < 2:
            painter.setPen(QPen(QColor(150, 150, 150), 1))
            painter.drawText(10, h // 2, "Not enough data yet")
            return

        pad_left, pad_right, pad_top, pad_bottom = 40, 10, 10, 20
        chart_w = w - pad_left - pad_right
        chart_h = h - pad_top - pad_bottom

        # Determine Y range from combined data (filter NaN/inf first)
        all_vals_raw = self._f0_means + self._f0_stds
        all_vals = [v for v in all_vals_raw if np.isfinite(v)]
        if not all_vals:
            painter.setPen(QPen(QColor(150, 150, 150), 1))
            painter.drawText(10, h // 2, "Invalid data")
            return
        y_min = max(0.0, min(all_vals) - 10.0)
        y_max = max(all_vals) + 10.0
        y_range = y_max - y_min or 1.0

        def x_pos(i: int) -> float:
            return pad_left + i / (n - 1) * chart_w

        def y_pos(v: float) -> float:
            return pad_top + (1.0 - (v - y_min) / y_range) * chart_h

        # Grid lines at y_min, midpoint, y_max
        painter.setPen(QPen(_COLOR_GRID, 1))
        for level in (y_min, (y_min + y_max) / 2, y_max):
            y = _safe_int(y_pos(level))
            painter.drawLine(pad_left, y, w - pad_right, y)

        # Y-axis label
        painter.setPen(QPen(QColor(160, 160, 160), 1))
        painter.drawText(2, pad_top + 8, f"{y_max:.0f}")
        painter.drawText(2, h - pad_bottom - 4, f"{y_min:.0f}")

        # F0 mean line (green) - only draw segments with finite endpoints
        painter.setPen(QPen(_COLOR_F0_LINE, 2))
        for i in range(n - 1):
            if all(np.isfinite(v) for v in (self._f0_means[i], self._f0_means[i + 1])):
                x1, x2 = x_pos(i), x_pos(i + 1)
                y1_f0, y2_f0 = y_pos(self._f0_means[i]), y_pos(self._f0_means[i + 1])
                painter.drawLine(
                    _safe_int(x1), _safe_int(y1_f0),
                    _safe_int(x2), _safe_int(y2_f0),
                )

        # F0 std dev line (yellow) - only draw segments with finite endpoints
        painter.setPen(QPen(_COLOR_STD_LINE, 2))
        for i in range(n - 1):
            if all(np.isfinite(v) for v in (self._f0_stds[i], self._f0_stds[i + 1])):
                x1, x2 = x_pos(i), x_pos(i + 1)
                y1_std, y2_std = y_pos(self._f0_stds[i]), y_pos(self._f0_stds[i + 1])
                painter.drawLine(
                    _safe_int(x1), _safe_int(y1_std),
                    _safe_int(x2), _safe_int(y2_std),
                )

        # X-axis week labels (every Nth week to avoid crowding)
        painter.setPen(QPen(QColor(160, 160, 160), 1))
        for i, label in enumerate(self._weeks):
            if i % _WEEK_LABEL_STRIDE == 0:
                painter.drawText(_safe_int(x_pos(i)) - 8, h - 4, label)


# --------------------------------------------------------------------------- #
# ProgressPanel
# --------------------------------------------------------------------------- #


class ProgressPanel(QWidget):
    """Displays streak, milestone badges, weekly chart, and session history."""

    def __init__(self, db_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._db_path = db_path

        # Streak label
        self._streak_label = QLabel()

        # Milestone badges (one per milestone, laid out horizontally, wrapped)
        self._badge_widgets: dict[str, QLabel] = {}
        badges_layout = QHBoxLayout()
        badges_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        for mid_val, name in _MILESTONE_NAMES.items():
            badge = QLabel()
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFixedSize(120, 60)
            badge.setWordWrap(True)
            self._badge_widgets[mid_val] = badge
            badges_layout.addWidget(badge)

        badges_scroll = QScrollArea()
        badges_container = QWidget()
        badges_container.setLayout(badges_layout)
        badges_scroll.setWidget(badges_container)
        badges_scroll.setWidgetResizable(True)
        badges_scroll.setFixedHeight(80)
        badges_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        badges_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Weekly chart
        self._chart = WeeklyChartWidget()
        self._chart.setFixedHeight(180)

        # Session history table (test seam: _history_table)
        self._history_table = QTableWidget()
        self._history_table.setColumnCount(len(_TABLE_COLUMNS))
        self._history_table.setHorizontalHeaderLabels(list(_TABLE_COLUMNS))
        # NoEditTriggers prevents all editing, no need for per-item setFlags
        self._history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._history_table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self._streak_label)
        layout.addWidget(badges_scroll)
        layout.addWidget(self._chart)
        layout.addWidget(self._history_table)

        self._populate()

    def refresh(self) -> None:
        """Re-query the DB and refresh all widgets.

        Note: Must be called from the GUI thread.
        """
        self._populate()

    # ---------------------------------------------------------------------- #
    # Private
    # ---------------------------------------------------------------------- #

    def _populate(self) -> None:
        """Load data from DB and update all child widgets."""
        sessions = get_all_sessions(self._db_path)
        streak = get_streak(self._db_path)

        self._streak_label.setText(f"🔥 Current streak: {streak} day{'s' if streak != 1 else ''}")
        self._update_badges(sessions)
        self._update_chart(sessions)
        self._update_table(sessions)

    def _update_badges(self, sessions: list[dict[str, Any]]) -> None:
        """Update milestone badge colours and labels."""
        # Find first date each milestone was earned
        earned_dates: dict[str, str] = {}
        # Iterate oldest first so we capture the first earned date
        for s in reversed(sessions):
            flags_raw = s.get("milestone_flags_json") or "{}"
            try:
                flags: dict[str, bool] = json.loads(flags_raw)
            except (json.JSONDecodeError, TypeError) as exc:
                _logger.warning(
                    "Failed to parse milestone_flags_json for session %r: %s",
                    s.get("id"), exc
                )
                flags = {}
            for mid_val, earned in flags.items():
                if earned and mid_val not in earned_dates:
                    earned_dates[mid_val] = s.get("date", "")

        for mid_val, badge in self._badge_widgets.items():
            name = _MILESTONE_NAMES[mid_val]
            if mid_val in earned_dates:
                badge.setText(f"🏆 {name}\n{earned_dates[mid_val]}")
                badge.setStyleSheet(
                    f"background-color: {_COLOR_EARNED.name()}; color: white; "
                    "border-radius: 4px; padding: 2px;"
                )
            else:
                badge.setText(f"{name}\n(not yet earned)")
                badge.setStyleSheet(
                    f"background-color: {_COLOR_UNEARNED.name()}; color: #cccccc; "
                    "border-radius: 4px; padding: 2px;"
                )

    def _update_chart(self, sessions: list[dict[str, Any]]) -> None:
        """Aggregate sessions by ISO week and update the chart."""
        # Group by ISO week
        weekly: dict[tuple[int, int], list[dict[str, Any]]] = {}
        for s in sessions:
            date_str = s.get("date")
            if not date_str:
                continue
            try:
                d = date.fromisoformat(date_str)
            except ValueError as exc:
                _logger.warning("Skipping session with invalid date %r: %s", date_str, exc)
                continue
            iso = d.isocalendar()
            key = (iso.year, iso.week)
            weekly.setdefault(key, []).append(s)

        if len(weekly) < 2:
            self._chart.set_data([], [], [])
            return

        sorted_keys = sorted(weekly.keys())
        week_labels: list[str] = []
        f0_means: list[float] = []
        f0_stds: list[float] = []

        for year, week in sorted_keys:
            week_sessions = weekly[(year, week)]
            f0_vals = [
                float(s["avg_f0"])
                for s in week_sessions
                if s.get("avg_f0") is not None
            ]
            std_vals = [
                float(s["f0_std_dev"])
                for s in week_sessions
                if s.get("f0_std_dev") is not None
            ]
            if not f0_vals:
                continue
            week_labels.append(f"W{week:02d}")
            f0_means.append(float(np.mean(f0_vals)))
            f0_stds.append(float(np.mean(std_vals)) if std_vals else float("nan"))

        self._chart.set_data(week_labels, f0_means, f0_stds)

    def _update_table(self, sessions: list[dict[str, Any]]) -> None:
        """Populate the session history QTableWidget."""
        self._history_table.setRowCount(0)
        for row_idx, s in enumerate(sessions):
            self._history_table.insertRow(row_idx)
            date_str = s.get("date") or ""
            dur_min = f"{float(s['duration_secs']) / 60:.1f}" if s.get("duration_secs") is not None else "—"
            avg_f0 = f"{float(s['avg_f0']):.1f}" if s.get("avg_f0") is not None else "—"
            f0_std = f"{float(s['f0_std_dev']):.1f}" if s.get("f0_std_dev") is not None else "—"
            avg_f2 = f"{float(s['avg_f2']):.1f}" if s.get("avg_f2") is not None else "—"

            for col_idx, text in enumerate((date_str, dur_min, avg_f0, f0_std, avg_f2)):
                item = QTableWidgetItem(text)
                self._history_table.setItem(row_idx, col_idx, item)
