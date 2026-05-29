"""sounddevice audio capture with lock-free deque + analysis thread.

Architecture:
  sounddevice callback   → deque (lock-free append/popleft)
  analysis thread        → reads deque, runs DSP, posts to results queue
  Qt main thread (30Hz)  → polls results queue via QTimer
"""
from __future__ import annotations
import queue
import threading
import time
from collections import deque
from dataclasses import dataclass

import numpy as np
import sounddevice as sd
import structlog
from scipy.signal import resample_poly

from switchedonvoice.audio.voice_detector import is_voiced
from switchedonvoice.audio.pitch import estimate_f0
from switchedonvoice.audio.formants import estimate_formants
from switchedonvoice.audio.spectrum import compute_spectrum
from switchedonvoice.audio.cpp import compute_cpp

_log = structlog.get_logger(__name__)

_SAMPLE_RATE_CAPTURE = 44100
_SAMPLE_RATE_LPC = 16000
_BUFFER_DURATION_S = 0.2       # 200 ms buffer fed to analysis
_ANALYSIS_INTERVAL_S = 0.033   # ~30 Hz analysis rate
_BLOCK_SIZE = 512
# 44100 Hz / 512-sample blocks ≈ 86 blocks/s. 2-second cap.
_DEQUE_MAX_BLOCKS = 172


@dataclass
class AnalysisResult:
    """Holds one analysis frame result for delivery to the UI."""
    f0: float | None
    formants: list[float]
    cpp: float | None
    is_voiced: bool
    spectrum_freqs: np.ndarray
    spectrum_db: np.ndarray
    raw_audio: np.ndarray | None = None  # the 200 ms buffer used for this frame; for waveform display


class AudioCapture:
    """Manages microphone capture and real-time DSP analysis.

    Usage:
        cap = AudioCapture(device_index=None, sample_rate=44100)
        cap.start()
        # poll cap.results (queue.Queue) in a QTimer at 30 Hz
        cap.stop()
    """

    def __init__(self, device_index: int | None, sample_rate: int = _SAMPLE_RATE_CAPTURE) -> None:
        self._device_index = device_index
        self._sample_rate = sample_rate
        self._buffer: deque[np.ndarray] = deque(maxlen=_DEQUE_MAX_BLOCKS)
        self.results: queue.Queue[AnalysisResult] = queue.Queue(maxsize=10)
        self._stream: sd.InputStream | None = None
        self._analysis_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start the microphone stream and analysis thread."""
        if self._analysis_thread is not None and self._analysis_thread.is_alive():
            raise RuntimeError("AudioCapture.start() called while already running")
        self._stop_event.clear()
        self._stream = sd.InputStream(
            device=self._device_index,
            samplerate=self._sample_rate,
            channels=1,
            dtype="float32",
            blocksize=_BLOCK_SIZE,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self._analysis_thread.start()

    def stop(self) -> None:
        """Stop the stream and analysis thread cleanly."""
        self._stop_event.set()
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if self._analysis_thread is not None:
            self._analysis_thread.join(timeout=2.0)
            if self._analysis_thread.is_alive():
                _log.error("audio_analysis_thread_did_not_stop", timeout_s=2.0)
            else:
                self._analysis_thread = None

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,  # noqa: ARG002
        time_info: object,  # noqa: ARG002
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            if status.input_overflow:
                _log.warning("audio_capture_input_overflow")
            else:
                _log.warning("audio_capture_status", status=str(status))
        # Minimal work in callback — just copy the block into the deque
        self._buffer.append(indata[:, 0].copy())

    def _analysis_loop(self) -> None:
        n_buffer_samples = int(self._sample_rate * _BUFFER_DURATION_S)
        while not self._stop_event.is_set():
            time.sleep(_ANALYSIS_INTERVAL_S)
            try:
                # Drain deque into a contiguous analysis buffer
                chunks: list[np.ndarray] = []
                while self._buffer:
                    chunks.append(self._buffer.popleft())
                if not chunks:
                    continue
                raw = np.concatenate(chunks)
                if len(raw) > n_buffer_samples:
                    raw = raw[-n_buffer_samples:]

                voiced = is_voiced(raw)
                f0 = estimate_f0(raw.astype(np.float64), self._sample_rate) if voiced else None

                # Downsample for LPC
                lpc_audio = resample_poly(raw, _SAMPLE_RATE_LPC, self._sample_rate).astype(np.float32)
                formants = estimate_formants(lpc_audio, _SAMPLE_RATE_LPC) if voiced else []

                cpp = compute_cpp(lpc_audio, _SAMPLE_RATE_LPC) if voiced else None
                freqs, db = compute_spectrum(raw, self._sample_rate)

                result = AnalysisResult(
                    f0=f0,
                    formants=formants,
                    cpp=cpp,
                    is_voiced=voiced,
                    spectrum_freqs=freqs,
                    spectrum_db=db,
                    raw_audio=raw,
                )
                try:
                    self.results.put_nowait(result)
                except queue.Full:
                    pass  # Drop frame — UI is behind. This is intentional.
            except Exception:
                _log.exception("audio_analysis_loop_error")
                # Keep the loop alive — do NOT re-raise
