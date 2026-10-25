"""
Core configuration for the EOG Early Intent Detection backend.
"""
from pathlib import Path
import os

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT

# Dataset path - try multiple locations
_candidates = [
    PROJECT_ROOT.parent / "data" / "Dataset_Isotropic",
    PROJECT_ROOT.parent / "Dataset_Isotropic" / "Dataset_Isotropic",
    Path("c:/Users/Admin/OneDrive/Desktop/AWS project/Dataset_Isotropic/Dataset_Isotropic"),
]
DATASET_ROOT = None
for c in _candidates:
    if c.exists():
        DATASET_ROOT = c
        break

ARTIFACTS_DIR = BACKEND_ROOT / "artifacts"
MODELS_DIR = ARTIFACTS_DIR / "models"
REPORTS_DIR = ARTIFACTS_DIR / "reports"
CACHE_DIR = ARTIFACTS_DIR / "cache"

# Ensure artifact directories exist
for d in [MODELS_DIR, REPORTS_DIR, CACHE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Signal constants
SAMPLING_RATE = 256  # Hz
SAMPLING_PERIOD_MS = 1000.0 / SAMPLING_RATE  # ~3.906 ms

# Dataset constants
EXPECTED_SUBJECTS = [f"S{i}" for i in range(1, 15)]
EXPECTED_CHANNELS = 16
EXPECTED_TRIALS_PER_SUBJECT = 288
EXPECTED_DIRECTIONS = 36
TARGET_MAGNITUDE_DEG = 12.0

# ControlSignal phase values
CS_OUTWARD = 1   # Centre → target saccade
CS_RETURN = 2    # Target → centre return
CS_BLINK = 3     # Blink/relaxation period
CS_TERMINATION = 30  # Recording termination marker (single sample, end of recording)

# Early observation windows (ms)
DEFAULT_WINDOW_DURATIONS_MS = [20, 40, 60, 80, 100, 120, 160, 200]

# Direction classification schemes
DIRECTION_LABELS_4 = ["Right", "Up", "Left", "Down"]
DIRECTION_LABELS_8 = [
    "Right", "Up-Right", "Up", "Up-Left",
    "Left", "Down-Left", "Down", "Down-Right"
]

# Random seed for reproducibility
RANDOM_SEED = 42
