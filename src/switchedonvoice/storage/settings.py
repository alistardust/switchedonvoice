"""Settings persistence via JSON."""
from __future__ import annotations
import json
import os
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path

_DEFAULT_SETTINGS_PATH = Path.home() / ".switchedonvoice" / "settings.json"


@dataclass
class Settings:
    """Application settings with sensible defaults."""
    device_index: int | None = None
    onboarding_complete: bool = False
    baseline_f0: float | None = None
    baseline_f0_std_dev: float | None = None
    baseline_f2: float | None = None
    noise_floor_rms: float | None = None
    f0_target_min: float = 185.0
    f0_target_max: float = 255.0


def load_settings(path: Path = _DEFAULT_SETTINGS_PATH) -> Settings:
    """Load settings from JSON file. Returns defaults if file is absent or corrupt."""
    if not path.exists():
        return Settings()
    try:
        data = json.loads(path.read_text())
        return Settings(
            device_index=data.get("device_index"),
            onboarding_complete=bool(data.get("onboarding_complete", False)),
            baseline_f0=data.get("baseline_f0"),
            baseline_f0_std_dev=data.get("baseline_f0_std_dev"),
            baseline_f2=data.get("baseline_f2"),
            noise_floor_rms=data.get("noise_floor_rms"),
            f0_target_min=float(data.get("f0_target_min", 185.0)),
            f0_target_max=float(data.get("f0_target_max", 255.0)),
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return Settings()


def save_settings(path: Path = _DEFAULT_SETTINGS_PATH, settings: Settings | None = None) -> None:
    """Write settings to JSON file atomically (temp file + rename).

    Args:
        path: Path to settings.json. Parent directories are created if absent.
        settings: Settings to write. Writes defaults if None.
    """
    if settings is None:
        settings = Settings()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path_str = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(tmp_fd, "w") as f:
            f.write(json.dumps(asdict(settings), indent=2))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
