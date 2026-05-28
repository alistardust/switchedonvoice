"""Vocal health warnings based on session elapsed time."""
from enum import Enum

_YELLOW_THRESHOLD_SECS: float = 45 * 60
_RED_THRESHOLD_SECS: float = 60 * 60


class WarningLevel(Enum):
    """Warning level for vocal health based on elapsed session time."""

    NONE = "none"
    YELLOW = "yellow"   # Consider taking a break
    RED = "red"         # Please rest your voice


def should_warn(elapsed_secs: float) -> WarningLevel:
    """Return the appropriate warning level for the given elapsed session time.

    Args:
        elapsed_secs: Total elapsed session time in seconds.

    Returns:
        WarningLevel.RED if >= 60 min, YELLOW if >= 45 min, else NONE.
    """
    if elapsed_secs >= _RED_THRESHOLD_SECS:
        return WarningLevel.RED
    if elapsed_secs >= _YELLOW_THRESHOLD_SECS:
        return WarningLevel.YELLOW
    return WarningLevel.NONE
