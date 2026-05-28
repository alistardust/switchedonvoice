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


def test_analysis_loop_runs_and_posts_result() -> None:
    """Real _analysis_loop should drain buffer and post an AnalysisResult."""
    from unittest.mock import patch

    cap = make_capture()
    sr = cap._sample_rate
    t = np.linspace(0, 0.2, int(sr * 0.2), dtype=np.float32)
    cap._buffer.append(np.sin(2 * np.pi * 200 * t) * 0.5)

    call_count = 0

    def stop_after_one() -> bool:
        nonlocal call_count
        call_count += 1
        return call_count > 1  # first check: run; second check: stop

    with patch("switchedonvoice.audio.capture.time.sleep"):
        cap._stop_event.is_set = stop_after_one  # type: ignore[method-assign]
        cap._analysis_loop()

    assert cap.results.qsize() == 1
    result = cap.results.get_nowait()
    assert isinstance(result, AnalysisResult)
    assert result.raw_audio is not None


def test_analysis_loop_survives_dsp_exception() -> None:
    """If DSP raises inside the loop, the exception is logged and the loop continues."""
    from unittest.mock import patch
    import switchedonvoice.audio.capture as capture_mod

    cap = make_capture()
    sr = cap._sample_rate
    t = np.linspace(0, 0.2, int(sr * 0.2), dtype=np.float32)
    cap._buffer.append(np.sin(2 * np.pi * 200 * t) * 0.5)

    call_count = 0

    def stop_after_one() -> bool:
        nonlocal call_count
        call_count += 1
        return call_count > 1

    with patch("switchedonvoice.audio.capture.time.sleep"), \
         patch.object(capture_mod, "is_voiced", side_effect=RuntimeError("dsp boom")):
        cap._stop_event.is_set = stop_after_one  # type: ignore[method-assign]
        cap._analysis_loop()  # must not raise

    # Loop completed without crashing; queue may be empty (exception before put)
    # The important thing is no exception propagated


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
