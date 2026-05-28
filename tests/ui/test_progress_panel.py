# tests/ui/test_progress_panel.py
"""Tests for ProgressPanel."""
import sys
import pytest
from datetime import date
from pathlib import Path
from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)


@pytest.fixture()
def db(tmp_path: Path):
    from switchedonvoice.storage.db import init_db
    p = tmp_path / "test.db"
    init_db(p)
    return p


def test_panel_constructs(qtbot, db):
    from switchedonvoice.ui.progress_panel import ProgressPanel
    panel = ProgressPanel(db_path=db)
    qtbot.addWidget(panel)
    assert panel is not None


def test_session_table_reflects_inserted_data(qtbot, db):
    from switchedonvoice.storage.sessions import create_session, close_session
    from switchedonvoice.ui.progress_panel import ProgressPanel

    sid = create_session(db)
    close_session(db, sid, duration_secs=300.0, avg_f0=185.0, f0_std_dev=28.0,
                  avg_f2=1850.0, milestone_flags={})

    panel = ProgressPanel(db_path=db)
    qtbot.addWidget(panel)
    table = panel._history_table   # access the QTableWidget via test seam
    assert table.rowCount() == 1

    # Columns: Date, Duration (min), Avg F0 (Hz), F0 Std Dev (Hz), Avg F2 (Hz)
    col_headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
    assert "F0 Std Dev (Hz)" in col_headers

    f0_col = col_headers.index("Avg F0 (Hz)")
    std_col = col_headers.index("F0 Std Dev (Hz)")
    f2_col  = col_headers.index("Avg F2 (Hz)")
    assert float(table.item(0, f0_col).text()) == pytest.approx(185.0, abs=0.1)
    assert float(table.item(0, std_col).text()) == pytest.approx(28.0, abs=0.1)
    assert float(table.item(0, f2_col).text()) == pytest.approx(1850.0, abs=0.1)
