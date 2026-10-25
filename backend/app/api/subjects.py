"""Subject and trial API routes."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.data.dataset_loader import get_loader
from app.data.trial_segmenter import segment_trials, get_trial_eog, get_direction_label_name
from app.core.config import SAMPLING_RATE
import numpy as np

router = APIRouter()


@router.get("/subjects")
async def list_subjects():
    """List all available subjects with summary metadata."""
    loader = get_loader()
    subjects = []
    for sid in loader.subject_ids:
        meta = loader.get_subject_metadata(sid)
        subjects.append({
            "subject_id": meta.subject_id,
            "n_channels": meta.n_channels,
            "n_samples": meta.n_samples,
            "duration_sec": meta.duration_sec,
            "n_trials": meta.n_trials,
            "pd": meta.pd,
            "dist_screen": meta.dist_screen,
        })
    return {"subjects": subjects}


@router.get("/subjects/{subject_id}/summary")
async def subject_summary(subject_id: str):
    """Get detailed summary for a specific subject."""
    loader = get_loader()
    if subject_id not in loader.subject_ids:
        raise HTTPException(404, f"Subject {subject_id} not found")

    meta = loader.get_subject_metadata(subject_id)
    return {
        "subject_id": meta.subject_id,
        "eog_shape": list(meta.eog_shape),
        "n_samples": meta.n_samples,
        "n_channels": meta.n_channels,
        "duration_sec": meta.duration_sec,
        "pd": meta.pd,
        "dist_screen": meta.dist_screen,
        "control_signal_values": meta.control_signal_values,
        "n_trials": meta.n_trials,
    }


@router.get("/subjects/{subject_id}/trials")
async def list_trials(subject_id: str):
    """List all trials for a subject with metadata."""
    loader = get_loader()
    if subject_id not in loader.subject_ids:
        raise HTTPException(404, f"Subject {subject_id} not found")

    trials = segment_trials(loader, subject_id)
    trial_list = []
    for t in trials:
        trial_list.append({
            "trial_id": t.trial_id,
            "outward_start": t.outward_start,
            "outward_end": t.outward_end,
            "return_start": t.return_start,
            "return_end": t.return_end,
            "blink_start": t.blink_start,
            "blink_end": t.blink_end,
            "target_horizontal_deg": t.target_horizontal_deg,
            "target_vertical_deg": t.target_vertical_deg,
            "target_angle_deg": t.target_angle_deg,
            "target_magnitude_deg": t.target_magnitude_deg,
            "direction_label_8": t.direction_label_8,
            "direction_label_8_name": get_direction_label_name(t.direction_label_8, 8),
            "direction_label_4": t.direction_label_4,
            "direction_label_36": t.direction_label_36,
        })
    return {"subject_id": subject_id, "n_trials": len(trial_list), "trials": trial_list}
