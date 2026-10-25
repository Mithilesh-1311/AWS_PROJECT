"""Versioned cue-triggered processor shared by experiments, serving and replay."""
from collections import deque
from time import perf_counter
import numpy as np
from scipy.signal import butter, sosfilt

from app.core.config import SAMPLING_RATE
from app.features.window_generator import ms_to_samples

VERSION = "causal-v1"
CALIBRATION_SAMPLES = 25
MAX_SAMPLES = 2048


class CausalProcessor:
    """One outward phase, fixed channels, 25-sample delayed calibration, no fallback."""

    def __init__(self, window_ms=100, alignment="onset", n_channels=16):
        if alignment not in {"cue", "onset"} or not 1 <= n_channels <= 16:
            raise ValueError("Unsupported alignment or channel count")
        if not 0 < window_ms <= 1000:
            raise ValueError("Window must be in (0, 1000] ms")
        self.n_window = ms_to_samples(window_ms)
        self.window_ms = window_ms
        self.alignment = alignment
        self.n_channels = n_channels
        self.raw_calibration = []
        self.baseline = None
        self.sos = butter(1, 0.1, btype="highpass", fs=SAMPLING_RATE, output="sos")
        self.zi = np.zeros((len(self.sos), n_channels, 2))
        self.filtered = deque(maxlen=MAX_SAMPLES)
        self.aggregate_history = deque(maxlen=3)
        self.last_smoothed = 0.0
        self.derivatives = []
        self.threshold = None
        self.crossing = None
        self.confirmation = None
        self.run_start = None
        self.run_length = 0
        self.next_sample = 0
        self.result = None
        self.processing_ms = 0.0

    def _filter(self, values):
        filtered, self.zi = sosfilt(self.sos, values, axis=1, zi=self.zi)
        return filtered

    def _observe(self, sample):
        self.filtered.append(sample.copy())
        self.aggregate_history.append(float(np.sqrt(np.mean(sample ** 2))))
        smoothed = sum(self.aggregate_history) / 3
        derivative = abs(smoothed - self.last_smoothed)
        self.last_smoothed = smoothed
        return derivative

    def push(self, chunk, start_sample):
        values = np.asarray(chunk, dtype=float)
        if values.ndim != 2 or values.shape[0] != self.n_channels or not 1 <= values.shape[1] <= 256:
            raise ValueError("Chunk must contain 1..256 samples with the configured channels")
        if start_sample != self.next_sample:
            raise ValueError("Gap or out-of-order chunk; reset the session")
        if self.next_sample + values.shape[1] > MAX_SAMPLES or not np.isfinite(values).all():
            raise ValueError("Nonfinite data or trial resource limit exceeded")
        started = perf_counter()
        for sample in values.T:
            index = self.next_sample
            self.next_sample += 1
            if self.baseline is None:
                self.raw_calibration.append(sample.copy())
                if len(self.raw_calibration) < CALIBRATION_SAMPLES:
                    continue
                calibration = np.asarray(self.raw_calibration).T
                self.baseline = calibration.mean(axis=1, keepdims=True)
                for calibrated in self._filter(calibration - self.baseline).T:
                    self.derivatives.append(self._observe(calibrated))
                noise = np.asarray(self.derivatives[3:])
                median = np.median(noise)
                mad = np.median(np.abs(noise - median)) * 1.4826
                self.threshold = float(median + 5 * max(mad, 1e-8))
            else:
                derivative = self._observe(self._filter(sample[:, None] - self.baseline)[:, 0])
                if self.confirmation is None and index <= 200:
                    if derivative > self.threshold:
                        if self.run_length == 0:
                            self.run_start = index
                        self.run_length += 1
                        if self.run_length == 3:
                            self.crossing = self.run_start
                            self.confirmation = index
                    else:
                        self.run_length = 0
            anchor = 0 if self.alignment == "cue" else self.crossing
            if self.result is None and anchor is not None:
                ready = max(CALIBRATION_SAMPLES - 1, anchor + self.n_window - 1,
                            self.confirmation or 0)
                if index >= ready:
                    window = np.asarray(self.filtered).T[:, anchor:anchor + self.n_window].copy()
                    self.result = {"window": window, "requested_ms": self.window_ms,
                                   "n_samples": self.n_window,
                                   "sample_budget_ms": self.n_window / SAMPLING_RATE * 1000,
                                   "sample_span_ms": (self.n_window - 1) / SAMPLING_RATE * 1000,
                                   "crossing_sample": self.crossing, "confirmation_sample": self.confirmation,
                                   "window_start_sample": anchor, "ready_sample": index,
                                   "cue_to_decision_ms": index / SAMPLING_RATE * 1000,
                                   "calibration_samples": CALIBRATION_SAMPLES,
                                   "calibration_budget_ms": CALIBRATION_SAMPLES / SAMPLING_RATE * 1000,
                                   "cue_to_onset_ms": self.crossing / SAMPLING_RATE * 1000 if self.crossing is not None else None,
                                   "onset_reliable": 13 <= self.crossing <= 128 if self.crossing is not None else None,
                                   "onset_policy": "accept confirmed crossing up to sample 200; timing reliability is heuristic",
                                   "confirmation_delay_ms": ((self.confirmation - self.crossing) / SAMPLING_RATE * 1000
                                                             if self.confirmation is not None else None),
                                   "preprocessing_version": VERSION, "alignment": self.alignment}
        self.processing_ms += (perf_counter() - started) * 1000
        return self.result

    def status(self):
        return "ready" if self.result else ("calibrating" if self.baseline is None else "waiting_for_window")


def causal_window(eog, window_ms=100, alignment="onset"):
    processor = CausalProcessor(window_ms, alignment, eog.shape[0])
    for start in range(0, eog.shape[1], 32):
        processor.push(eog[:, start:start + 32], start)
        if processor.result:
            result = dict(processor.result)
            result["processing_ms"] = processor.processing_ms
            return result
    return None
