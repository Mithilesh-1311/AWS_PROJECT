"""
Dataset Loader
==============
Lazy-loading, cached access to the University of Malta EOG Isotropic dataset.
All 16 channels are retained. Raw .mat files remain on disk.
"""
import numpy as np
from scipy.io import loadmat
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from functools import lru_cache
from collections import OrderedDict
import threading
import logging

from app.core.config import (
    DATASET_ROOT, EXPECTED_SUBJECTS, EXPECTED_CHANNELS,
    SAMPLING_RATE, CS_OUTWARD, CS_RETURN, CS_BLINK, CS_TERMINATION
)

logger = logging.getLogger(__name__)


@dataclass
class SubjectMetadata:
    """Lightweight metadata for a subject (no signal data)."""
    subject_id: str
    eog_shape: Tuple[int, int]
    n_samples: int
    n_channels: int
    duration_sec: float
    pd: float  # inter-pupillary distance (m)
    dist_screen: float  # screen distance (m)
    control_signal_values: List[int] = field(default_factory=list)
    n_trials: int = 0


@dataclass
class TrialMetadata:
    """Metadata for a single trial segment."""
    subject_id: str
    trial_id: int
    # Sample indices (absolute, 0-based)
    outward_start: int
    outward_end: int  # exclusive
    return_start: int
    return_end: int    # exclusive
    blink_start: int
    blink_end: int     # exclusive
    # Target information
    target_horizontal_deg: float
    target_vertical_deg: float
    target_angle_deg: float       # atan2-based, 0-360
    target_magnitude_deg: float
    # Derived labels
    direction_label_36: int       # 0-35 index
    direction_label_8: int        # 0-7 index
    direction_label_4: int        # 0-3 index


class DatasetLoader:
    """Lazy-loading dataset manager for the EOG Isotropic dataset."""

    def __init__(self, dataset_root: Optional[Path] = None):
        self.root = Path(dataset_root) if dataset_root else DATASET_ROOT
        if self.root and (self.root / "Dataset_Isotropic" / "S1").is_dir():
            self.root = self.root / "Dataset_Isotropic"
        if self.root is None or not self.root.exists():
            raise FileNotFoundError(
                f"Dataset not found at {self.root}. "
                "Place the Dataset_Isotropic folder under data/ or configure DATASET_ROOT."
            )
        # Bound retained MATLAB arrays to ten files (at most two complete subjects).
        self._subject_cache = OrderedDict()
        self._lock = threading.RLock()
        self._metadata_cache = {}
        self._trial_cache: Dict[str, List[TrialMetadata]] = {}
        logger.info(f"DatasetLoader initialized: {self.root}")

    @property
    def subject_ids(self) -> List[str]:
        """Return sorted list of available subject IDs."""
        available = []
        for sid in EXPECTED_SUBJECTS:
            if (self.root / sid).exists():
                available.append(sid)
        return sorted(available, key=lambda x: int(x[1:]))

    def _load_mat(self, subject_id: str, filename: str) -> dict:
        """Load a .mat file for a subject, with caching."""
        if subject_id not in self.subject_ids:
            raise ValueError("Unknown subject identifier")
        if filename not in {"EOG.mat", "ControlSignal.mat", "Target_GA_stream.mat", "PD.mat", "Dist_screen.mat"}:
            raise ValueError("Unknown dataset file")
        cache_key = f"{subject_id}/{filename}"
        with self._lock:
            if cache_key not in self._subject_cache:
                fpath = self.root / subject_id / filename
                if not fpath.exists():
                    raise FileNotFoundError(f"Missing {subject_id}/{filename}")
                data = loadmat(str(fpath), squeeze_me=True)
                key = filename[:-4]
                if key not in data or not np.isfinite(data[key]).all():
                    raise ValueError(f"Invalid or nonfinite {subject_id}/{filename}")
                self._subject_cache[cache_key] = data
            self._subject_cache.move_to_end(cache_key)
            data = self._subject_cache[cache_key]
            while len(self._subject_cache) > 10:
                self._subject_cache.popitem(last=False)
            return data

    def get_eog(self, subject_id: str) -> np.ndarray:
        """Load EOG data: shape (16, n_samples), float64."""
        data = self._load_mat(subject_id, "EOG.mat")
        eog = data["EOG"]
        if eog.ndim == 1:
            eog = eog.reshape(1, -1)
        if eog.ndim != 2 or eog.shape[0] != EXPECTED_CHANNELS:
            raise ValueError("EOG must have shape (16, samples)")
        return eog

    def get_control_signal(self, subject_id: str) -> np.ndarray:
        """Load ControlSignal: shape (n_samples,), uint8."""
        data = self._load_mat(subject_id, "ControlSignal.mat")
        cs = data["ControlSignal"]
        return cs.flatten()

    def get_target_ga_stream(self, subject_id: str) -> np.ndarray:
        """Load Target_GA_stream: shape (2, n_samples).
        Row 0 = horizontal, Row 1 = vertical."""
        data = self._load_mat(subject_id, "Target_GA_stream.mat")
        tga = data["Target_GA_stream"]
        if tga.ndim == 1:
            tga = tga.reshape(1, -1)
        return tga

    def get_pd(self, subject_id: str) -> float:
        """Get inter-pupillary distance (meters)."""
        data = self._load_mat(subject_id, "PD.mat")
        return float(np.squeeze(data["PD"]))

    def get_dist_screen(self, subject_id: str) -> float:
        """Get screen distance (meters)."""
        data = self._load_mat(subject_id, "Dist_screen.mat")
        return float(np.squeeze(data["Dist_screen"]))

    def get_subject_metadata(self, subject_id: str) -> SubjectMetadata:
        """Get lightweight subject metadata without loading full EOG."""
        signature = tuple((self.root / subject_id / name).stat().st_mtime_ns for name in ["EOG.mat", "ControlSignal.mat", "Target_GA_stream.mat", "PD.mat", "Dist_screen.mat"])
        cached = self._metadata_cache.get(subject_id)
        if cached and cached[0] == signature:
            return cached[1]
        eog = self.get_eog(subject_id)
        cs = self.get_control_signal(subject_id)

        from app.data.trial_segmenter import segment_trials
        n_trials = len(segment_trials(self, subject_id))

        metadata = SubjectMetadata(
            subject_id=subject_id,
            eog_shape=eog.shape,
            n_samples=eog.shape[1],
            n_channels=eog.shape[0],
            duration_sec=round(eog.shape[1] / SAMPLING_RATE, 2),
            pd=self.get_pd(subject_id),
            dist_screen=self.get_dist_screen(subject_id),
            control_signal_values=sorted(np.unique(cs).tolist()),
            n_trials=n_trials,
        )
        self._metadata_cache[subject_id] = (signature, metadata)
        return metadata

    def release_subject(self, subject_id: str):
        """Release cached data for a subject to free memory."""
        with self._lock:
            for key in list(self._subject_cache):
                if key.startswith(subject_id + "/"):
                    del self._subject_cache[key]
            self._trial_cache.pop(subject_id, None)

    def release_all(self):
        """Release all cached data."""
        with self._lock:
            self._subject_cache.clear()
            self._trial_cache.clear()


# Module-level singleton
_loader_instance: Optional[DatasetLoader] = None


def get_loader() -> DatasetLoader:
    """Get or create the singleton DatasetLoader instance."""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = DatasetLoader()
    return _loader_instance
