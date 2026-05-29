---
phase: 21-settings-panel
reviewed: 2025-01-16T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - src/switchedonvoice/storage/settings.py
  - src/switchedonvoice/ui/pitch_meter.py
  - src/switchedonvoice/onboarding/baseline_dialog.py
  - src/switchedonvoice/ui/settings_panel.py
  - tests/onboarding/test_baseline_dialog.py
findings:
  critical: 2
  warning: 3
  info: 2
  total: 7
status: issues_found
---

# Task 21 Spec Compliance Review: Settings Panel

**Reviewed:** 2025-01-16T00:00:00Z  
**Depth:** standard  
**Files Reviewed:** 5  
**Status:** ❌ SPEC GAPS FOUND  

## Summary

The Settings Panel implementation provides most required functionality: device selector with persist, F0 target range spinboxes, and baseline re-record dialog integration. However, **critical spec gaps exist** in the pitch meter zone handling. The F0 target min/max values are stored in Settings and configurable via spinboxes, but:

1. **The pitch meter's green zone remains hardcoded** (185–255 Hz) and does not dynamically reflect the user-configured F0 target values from Settings.
2. The `set_f0_target_range()` setter exists but is never called, and even if called, wouldn't change the displayed zones because `f0_zone_color()` uses hardcoded boundaries.
3. **No integration path** exists between the SettingsPanel F0 spinboxes and the PitchMeterWidget — the values are saved to Settings but never passed to the meter for display.

Additionally, a **critical error-handling bug** exists in `load_settings()` where `ValueError` is not caught, causing the app to crash if settings.json contains invalid F0 target values.

---

## Critical Issues

### CR-01: ValueError Not Caught in load_settings() — Settings Crash on Corrupt JSON

**File:** `src/switchedonvoice/storage/settings.py:41`

**Issue:**  
The `load_settings()` function converts settings values using `float()` but does not catch `ValueError`. If `settings.json` contains invalid F0 target values (e.g., `"f0_target_min": "invalid"`), the `float()` conversion crashes the app instead of falling back to defaults.

**Current code (line 38–42):**
```python
f0_target_min=float(data.get("f0_target_min", 185.0)),
f0_target_max=float(data.get("f0_target_max", 255.0)),
)
except (json.JSONDecodeError, KeyError, TypeError):
    return Settings()
```

**Impact:**  
- User settings corruption or manual JSON edits cause application crash.
- No graceful fallback to defaults.

**Fix:**
```python
except (json.JSONDecodeError, KeyError, TypeError, ValueError):
    return Settings()
```

---

### CR-02: PitchMeterWidget F0 Target Zones Not Dynamic — Spec Violation

**File:** `src/switchedonvoice/ui/pitch_meter.py:20–26, 95`

**Issue:**  
The spec explicitly requires: *"The pitch meter zones in `pitch_meter.py` should read these values from `Settings` rather than hardcoding the boundaries."*

Current implementation:
- **Lines 20–26:** `_ZONES` list hardcodes green zone as `(185.0, 256.0, QColor(60, 200, 100))`
- **Line 95:** `paintEvent()` calls `color = f0_zone_color(self._f0)`, which uses only the hardcoded `_ZONES`
- **Lines 47–48, 78–79:** Instance variables `_f0_target_min` and `_f0_target_max` are stored but **never used** in color determination
- **Lines 64–80:** `set_f0_target_range()` setter exists but is meaningless because the zones still don't change

**Evidence:**  
Tested by searching for usage of `_f0_target_min` and `_f0_target_max` in `paintEvent()` — both instance variables are never referenced in zone coloring logic.

**Impact:**  
- Users cannot configure the "feminine target range" (green zone) via SettingsPanel F0 spinboxes
- The 185–255 Hz target zone is fixed regardless of user Settings
- Violates spec requirement for dynamic zones based on user-configurable min/max

**Fix:**
Modify `f0_zone_color()` to accept min/max parameters and dynamically compute zones:
```python
def f0_zone_color(f0: float, f0_target_min: float = 185.0, f0_target_max: float = 255.0) -> QColor:
    """Return the display colour for a given F0 value."""
    zones = [
        (0.0, 120.0, QColor(120, 0, 0)),
        (120.0, 165.0, QColor(200, 60, 60)),
        (165.0, f0_target_min, QColor(220, 200, 60)),
        (f0_target_min, f0_target_max, QColor(60, 200, 100)),  # Dynamic target zone
        (f0_target_max, 1200.0, QColor(80, 160, 255)),
    ]
    for low, high, color in zones:
        if low <= f0 < high:
            return color
    return zones[-1][2]
```

Then update `paintEvent()` to pass instance variables:
```python
color = f0_zone_color(self._f0, self._f0_target_min, self._f0_target_max)
```

---

## Warnings

### WR-01: SettingsPanel F0 Target Values Never Passed to PitchMeterWidget

**File:** `src/switchedonvoice/ui/settings_panel.py`  
**Related:** `src/switchedonvoice/ui/analysis_panel.py:23`

**Issue:**  
- **SettingsPanel** defines F0 target spinboxes (lines 60–72) and persists them to Settings (lines 141–142)
- **AnalysisPanel** creates a `PitchMeterWidget` (line 23) but never calls `set_f0_target_range()`
- No integration path exists to propagate user-configured F0 values from Settings to the pitch meter display

**Impact:**  
Even after CR-02 is fixed, the F0 target values will never reach the PitchMeterWidget because SettingsPanel doesn't communicate them. This requires MainWindow or similar to connect the signal flow (e.g., `device_changed` signal should trigger pitch meter re-configuration).

**Fix:**  
Establish integration in MainWindow:
```python
# Pseudocode
settings_panel.device_changed.connect(self._on_settings_changed)

def _on_settings_changed(self):
    settings = load_settings()
    self._analysis_panel._pitch.set_f0_target_range(
        settings.f0_target_min, 
        settings.f0_target_max
    )
```

---

### WR-02: F0 Target Min/Max Validation No User Feedback

**File:** `src/switchedonvoice/ui/settings_panel.py:127–133`

**Issue:**  
When `f0_min >= f0_max`, the save is aborted with only a log message:
```python
if f0_min >= f0_max:
    _logger.warning("F0 target min (%s) must be less than max (%s) — save aborted", ...)
    return
```

User has no UI feedback (e.g., QMessageBox) explaining why the save failed. QSpinBox ranges (80–400 for min, 80–800 for max) allow invalid combinations like min=400, max=100.

**Impact:**  
Poor UX: silent failure with no user notification.

**Fix:**
Add user-facing error dialog:
```python
if f0_min >= f0_max:
    QMessageBox.warning(self, "Invalid F0 Range", 
                        f"F0 target min ({f0_min} Hz) must be less than max ({f0_max} Hz).")
    return
```

---

### WR-03: Minimal Test Coverage — test_baseline_dialog.py

**File:** `tests/onboarding/test_baseline_dialog.py:5–9`

**Issue:**  
The test is a smoke test that only asserts the dialog can be constructed:
```python
def test_baseline_dialog_constructs(qtbot):
    from switchedonvoice.onboarding.baseline_dialog import BaselineRecordingDialog
    dlg = BaselineRecordingDialog(device_index=None)
    qtbot.addWidget(dlg)
    assert dlg is not None
```

No assertions on dialog properties, signal behavior, or button functionality.

**Impact:**  
Low test confidence. The dialog could have broken UI layout or non-functional buttons and tests would pass.

**Fix:**  
Add substantive assertions:
```python
def test_baseline_dialog_constructs(qtbot):
    from switchedonvoice.onboarding.baseline_dialog import BaselineRecordingDialog
    dlg = BaselineRecordingDialog(device_index=None)
    qtbot.addWidget(dlg)
    
    # Assert dialog properties
    assert dlg is not None
    assert dlg.windowTitle() == "Record Vocal Baseline"
    assert dlg.isModal() is True
    
    # Assert buttons exist
    assert dlg._record_button is not None
    assert dlg._close_button is not None
    
    # Assert progress bar is initialized
    assert dlg._progress.maximum() == 30
    assert dlg._progress.value() == 0
```

---

## Info

### IN-01: Defensive Fallback in Device Query Not Necessary

**File:** `src/switchedonvoice/ui/settings_panel.py:114`

**Issue:**  
```python
self._device_combo.addItem(label, userData=dev.get("index", i))
```

The fallback to loop index `i` is unnecessary — `sounddevice.query_devices()` always includes an `"index"` key in each device dict.

**Impact:**  
Code clarity: minor. The fallback adds defensive programming that isn't needed.

**Fix:**
```python
self._device_combo.addItem(label, userData=dev["index"])
```

---

### IN-02: Incomplete Phase 1 Implementation — Baseline Dialog Recording Disabled

**File:** `src/switchedonvoice/onboarding/baseline_dialog.py:70–74`

**Issue:**  
The dialog is a placeholder for Phase 1:
```python
def _on_record_clicked(self) -> None:
    """Handle record button click — placeholder for Task 24 wiring."""
    self._record_button.setEnabled(False)
    self._status_label.setText("Recording… (live audio capture wired in Task 24)")
```

Recording is simulated, not functional. This is a known Phase 1 limitation.

**Impact:**  
User awareness: the dialog clearly signals that recording is not yet wired (good). No code defect — this is expected per spec ("In Phase 1 the recording is simulated").

**Note:**  
This is acceptable for Phase 1 but should be marked as a Known Limitation in Phase 1 Summary.

---

## Specification Compliance Matrix

| Requirement | Status | Notes |
|---|---|---|
| Device selector (QComboBox) | ✅ | Populated from `sounddevice.query_devices()` |
| Save button | ✅ | Present and wired |
| Re-record baseline button | ✅ | Opens modal BaselineRecordingDialog |
| `device_changed` signal | ✅ | Emitted when device saved and changed |
| Populate on `__init__` | ✅ | Called at line 93 |
| Populate on "Refresh" button | ✅ | Connected at line 49 |
| Persist device via `save_settings()` | ✅ | Persisted at line 145 |
| F0 target min/max spinboxes | ✅ | Present with defaults 185/255 Hz |
| Store in Settings | ✅ | `f0_target_min` and `f0_target_max` in Settings dataclass |
| Persist on save | ✅ | Saved at lines 141–142 |
| **PitchMeterWidget reads from Settings** | ❌ | **CRITICAL GAP**: Zones hardcoded, instance vars unused |
| Re-record baseline opens dialog | ✅ | Modal dialog at line 159 |
| BaselineRecordingDialog extracted | ✅ | In `onboarding/baseline_dialog.py` |
| Test: dialog constructs | ✅ | Passes, though minimal coverage |

**Overall: ❌ SPEC GAPS FOUND**

---

_Reviewed: 2025-01-16T00:00:00Z_  
_Reviewer: gsd-code-reviewer_  
_Depth: standard_
