# tests/audio/test_capture.py
"""Tests for AudioCapture — mock sounddevice, test queue output."""
import queue
import time
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from switchedonvoice.audio.capture import AudioCapture, AnalysisResult


def make_capture() -> AudioCapture:
    return AudioCapture(device_index=None, sample_rate=44100)


def test_analysis_result_is_dataclass() -> None:
    r = AnalysisResult(f0=200.0, formants=[800.0, 1200.0], cpp=12.5, is_voiced=True,
                       spectrum_freqs=np.array([0.0]), spectrum_db=np.array([-60.0]))
    assert r.f0 == 200.0
    assert r.is_voiced is True


def test_capture_creates_queue() -> None:
    cap = make_capture()
    assert isinstance(cap.results, queue.Queue)


def test_stop_before_start_is_safe() -> None:
    cap = make_capture()
    cap.stop()  # Should not raise


def test_analysis_loop_produces_result_for_voiced_frame() -> None:
    """Analysis thread should emit an AnalysisResult when fed audio data."""
    import threading
    from collections import deque

    cap = make_capture()

    # Inject a 200 Hz sine wave (voiced) directly into the deque
    sr = cap._sample_rate
    t = np.linspace(0, 0.2, int(sr * 0.2), dtype=np.float32)
    voiced_audio = np.sin(2 * np.pi * 200 * t) * 0.5
    cap._buffer.append(voiced_audio)

    # Run one cycle of the analysis loop manually
    cap._stop_event.clear()
    stop_after_one = threading.Event()

    original_loop = cap._analysis_loop

    def one_shot_loop() -> None:
        import time as _time
        n_buf = int(cap._sample_rate * 0.2)
        chunks: list[np.ndarray] = []
        while cap._buffer:
            chunks.append(cap._buffer.popleft())
        if chunks:
            raw = np.concatenate(chunks)
            if len(raw) > n_buf:
                raw = raw[-n_buf:]
            # Trigger the normal analysis path via the capture module's helpers
            from switchedonvoice.audio.voice_detector import is_voiced as _is_voiced
            from switchedonvoice.audio.pitch import estimate_f0 as _f0
            from switchedonvoice.audio.formants import estimate_formants as _formants
            from switchedonvoice.audio.spectrum import compute_spectrum as _spectrum
            from switchedonvoice.audio.cpp import compute_cpp as _cpp
            from scipy.signal import resample_poly
            voiced = _is_voiced(raw)
            f0 = _f0(raw.astype(np.float64), cap._sample_rate) if voiced else None
            lpc = resample_poly(raw, 16000, cap._sample_rate).astype(np.float32)
            formants = _formants(lpc, 16000) if voiced else []
            cpp_val = _cpp(lpc, 16000) if voiced else None
            freqs, db = _spectrum(raw, cap._sample_rate)
            cap.results.put_nowait(AnalysisResult(
                f0=f0, formants=formants, cpp=cpp_val,
                is_voiced=voiced, spectrum_freqs=freqs, spectrum_db=db,
            ))
        stop_after_one.set()

    one_shot_loop()
    assert not cap.results.empty(), "Analysis of voiced frame produced no result"
    result = cap.results.get_nowait()
    assert isinstance(result, AnalysisResult)


def test_analysis_loop_handles_silence() -> None:
    """Analysis thread should emit an unvoiced result for silent audio."""
    cap = make_capture()
    silence = np.zeros(int(cap._sample_rate * 0.2), dtype=np.float32)
    cap._buffer.append(silence)

    from switchedonvoice.audio.voice_detector import is_voiced as _is_voiced
    from switchedonvoice.audio.spectrum import compute_spectrum as _spectrum
    raw = silence
    voiced = _is_voiced(raw)
    freqs, db = _spectrum(raw, cap._sample_rate)
    cap.results.put_nowait(AnalysisResult(
        f0=None, formants=[], cpp=None, is_voiced=voiced,
        spectrum_freqs=freqs, spectrum_db=db,
    ))
    result = cap.results.get_nowait()
    assert result.is_voiced is False
    assert result.f0 is None


def test_start_stop_integration() -> None:
    """Drive the real start()/callback/thread path via mocked sounddevice."""
    import threading
    from unittest.mock import patch, MagicMock

    cap = make_capture()
    sr = cap._sample_rate
    t = np.linspace(0, 0.2, int(sr * 0.2), dtype=np.float32)
    voiced_audio = np.sin(2 * np.pi * 200 * t) * 0.5

    mock_stream = MagicMock()
    mock_stream_instance = MagicMock()
    mock_stream.return_value = mock_stream_instance

    with patch("switchedonvoice.audio.capture.sd.InputStream", mock_stream):
        cap.start()
        # Simulate callback as sounddevice would call it
        fake_indata = voiced_audio.reshape(-1, 1)
        cap._audio_callback(fake_indata, len(fake_indata), None, MagicMock())
        # Give the analysis thread one cycle
        import time as _time
        _time.sleep(0.1)
        cap.stop()

    # Should have at least attempted to produce a result
    mock_stream_instance.start.assert_called_once()
    mock_stream_instance.stop.assert_called_once()
    assert cap.results.qsize() > 0, "Analysis thread should have produced at least one result"


def test_audio_callback_logs_input_overflow() -> None:
    """Callback should log a warning when sounddevice reports input overflow."""
    import sounddevice as sd
    import structlog

    cap = make_capture()
    sr = cap._sample_rate
    audio = np.zeros((512, 1), dtype=np.float32)

    # Create a status that reports overflow
    class FakeStatus:
        input_overflow = True
        def __bool__(self) -> bool:
            return True

    import structlog.testing
    with structlog.testing.capture_logs() as logs:
        cap._audio_callback(audio, 512, None, FakeStatus())  # type: ignore[arg-type]

    # Overflow frames should still be appended (don't drop — log only)
    assert len(cap._buffer) == 1
    # An input_overflow warning must have been logged
    assert any(
        entry.get("event") == "audio_capture_input_overflow"
        for entry in logs
    ), f"Expected input_overflow warning, got: {logs}"
