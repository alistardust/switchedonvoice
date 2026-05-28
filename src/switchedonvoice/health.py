"""Vocal health warnings based on session elapsed time."""
from enum import Enum

_YELLOW_THRESHOLD_SECS: int = 45 * 60
_RED_THRESHOLD_SECS: int = 60 * 60


class WarningLevel(Enum):
    """Warning level for vocal health based on elapsed session time."""

    NONE = "none"
    YELLOW = "yellow"   # Consider taking a break
    RED = "red"         # Please rest your voice


def should_warn(elapsed_secs: float) -> WarningLevel:
    """Return the appropriate warning level for the given elapsed session time.

    Args:
        elapsed_secs: Total elapsed session time in seconds. Must be non-negative.

    Returns:
        WarningLevel.RED if >= 60 min, YELLOW if >= 45 min, else NONE.

    Raises:
        ValueError: If elapsed_secs is negative.
    """
    if elapsed_secs < 0:
        raise ValueError(f"elapsed_secs must be non-negative, got {elapsed_secs}")
    if elapsed_secs >= _RED_THRESHOLD_SECS:
        return WarningLevel.RED
    if elapsed_secs >= _YELLOW_THRESHOLD_SECS:
        return WarningLevel.YELLOW
    return WarningLevel.NONE
