"""Exercise panel: scrollable list of guided voice training exercises."""
from __future__ import annotations
from typing import TypedDict
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# --------------------------------------------------------------------------- #
# Exercise data
# --------------------------------------------------------------------------- #

class ExerciseData(TypedDict):
    """Schema for a single exercise entry."""
    name: str
    description: str
    technique: str


EXERCISES: list[ExerciseData] = [
    {
        "name": "Pitch Slide",
        "description": "Slide your pitch smoothly into your target zone and hold.",
        "technique": (
            "Start at your habitual pitch. Imagine your voice becoming lighter and smaller. "
            "Slide upward into your target zone and hold it steady for 5 seconds. "
            "Watch the pitch meter bar — aim for the green zone."
        ),
    },
    {
        "name": "Vowel Resonance",
        "description": "Shift your vowel resonance forward to raise F2.",
        "technique": (
            "Say 'ee' (as in 'see') with a bright, forward feeling in your mouth. "
            "Raise the front of your tongue toward your hard palate while sustaining the sound. "
            "Watch the F2 dot on the vowel map move right and up."
        ),
    },
    {
        "name": "Free Practice",
        "description": "Talk, read aloud, or experiment freely.",
        "technique": (
            "No rules — talk, read aloud, or experiment. "
            "Watch the meters and notice what changes your voice. "
            "This session is recorded for your progress history."
        ),
    },
]

# Durations per exercise in seconds; None means no time limit.
_DURATIONS: dict[str, int | None] = {
    "Pitch Slide": 30,
    "Vowel Resonance": 30,
    "Free Practice": None,
}

# --------------------------------------------------------------------------- #
# ExerciseCard widget
# --------------------------------------------------------------------------- #


class ExerciseCard(QFrame):
    """A single exercise card with title, description, technique, and timer."""

    def __init__(self, exercise: ExerciseData, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        if exercise["name"] not in _DURATIONS:
            raise KeyError(
                f"Exercise '{exercise['name']}' has no entry in _DURATIONS; "
                "add it before creating an ExerciseCard."
            )
        self._duration: int | None = _DURATIONS[exercise["name"]]
        self._remaining: int = self._duration or 0

        # Title
        title = QLabel(exercise["name"])
        title_font = title.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 2)
        title.setFont(title_font)

        # Description
        desc = QLabel(exercise["description"])
        desc.setWordWrap(True)

        # Technique
        technique = QLabel(exercise["technique"])
        technique.setWordWrap(True)
        technique.setStyleSheet("color: #aaaaaa;")

        # Timer controls (public attributes required by tests)
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self._on_start_stop)

        self.countdown_label = QLabel(self._countdown_text())
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.completion_label = QLabel("Done! 🎉")
        self.completion_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.completion_label.setVisible(False)

        # QTimer (1-second tick)
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(technique)
        layout.addWidget(self.start_button)
        layout.addWidget(self.countdown_label)
        layout.addWidget(self.completion_label)

    # ---------------------------------------------------------------------- #
    # Private helpers
    # ---------------------------------------------------------------------- #

    def _countdown_text(self) -> str:
        """Return the current countdown label text."""
        if self._duration is None:
            return ""
        return f"{self._remaining}s"

    def _on_start_stop(self) -> None:
        """Toggle between Start and Stop states."""
        if self.start_button.text() == "Start":
            self._remaining = self._duration or 0
            self.countdown_label.setText(self._countdown_text())
            self.completion_label.setVisible(False)
            self.start_button.setText("Stop")
            if self._duration is not None and not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()
            self._remaining = self._duration or 0
            self.countdown_label.setText(self._countdown_text())
            self.completion_label.setVisible(False)
            self.start_button.setText("Start")

    def _on_tick(self) -> None:
        """Called every second while timer is running."""
        self._remaining -= 1
        self.countdown_label.setText(self._countdown_text())
        if self._remaining <= 0:
            self._timer.stop()
            self._on_timer_complete()

    def _on_timer_complete(self) -> None:
        """Called when the exercise duration has elapsed."""
        self._timer.stop()
        self._remaining = self._duration or 0
        self.countdown_label.setText(self._countdown_text())
        self.completion_label.setVisible(True)
        self.start_button.setText("Start")


# --------------------------------------------------------------------------- #
# ExercisePanel (scrollable container)
# --------------------------------------------------------------------------- #


class ExercisePanel(QWidget):
    """Scrollable panel listing all exercise cards."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        for exercise in EXERCISES:
            layout.addWidget(ExerciseCard(exercise))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
