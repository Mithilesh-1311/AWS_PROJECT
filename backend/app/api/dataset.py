"""Dataset summary and overview API routes."""
from fastapi import APIRouter, HTTPException
from app.data.dataset_loader import get_loader
from app.core.config import (
    EXPECTED_SUBJECTS, EXPECTED_CHANNELS, SAMPLING_RATE,
    EXPECTED_TRIALS_PER_SUBJECT, EXPECTED_DIRECTIONS, TARGET_MAGNITUDE_DEG,
    DEFAULT_WINDOW_DURATIONS_MS
)
from app.features.window_generator import get_window_specs

router = APIRouter()


@router.get("/dataset/summary")
def dataset_summary():
    """Get overall dataset summary statistics."""
    try:
        loader = get_loader()
        subjects = loader.subject_ids
        from app.data.trial_segmenter import segment_trials
        total_trials = sum(loader.get_subject_metadata(sid).n_trials for sid in subjects)

        window_specs = get_window_specs()

        return {
            "n_subjects": len(subjects),
            "subject_ids": subjects,
            "n_channels": EXPECTED_CHANNELS,
            "sampling_rate_hz": SAMPLING_RATE,
            "expected_trials_per_subject": EXPECTED_TRIALS_PER_SUBJECT,
            "total_trials": total_trials,
            "n_directions": EXPECTED_DIRECTIONS,
            "target_magnitude_deg": TARGET_MAGNITUDE_DEG,
            "acquisition_filters": {
                "lowpass_hz": 30,
                "notch_hz": 50,
            },
            "window_specs": [s.to_dict() for s in window_specs],
        }
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Dataset unavailable; configure EOG_DATASET_ROOT")
