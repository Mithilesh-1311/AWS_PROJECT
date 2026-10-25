"""Data quality and validation API routes."""
from fastapi import APIRouter, HTTPException
import json
import logging
import numpy as np
from app.data.dataset_loader import get_loader
from app.data.trial_segmenter import segment_trials
from app.core.config import (
    REPORTS_DIR, EXPECTED_SUBJECTS, EXPECTED_CHANNELS,
    EXPECTED_TRIALS_PER_SUBJECT, CS_TERMINATION, SAMPLING_RATE
)

router = APIRouter()


@router.get("/data-quality")
def data_quality_report():
    """Generate live data quality assessment for all subjects."""
    loader = get_loader()
    if not loader.subject_ids:
        raise HTTPException(503, "Dataset unavailable")
    subjects_report = []
    total_anomalies = []

    for sid in loader.subject_ids:
        try:
            meta = loader.get_subject_metadata(sid)
            cs = loader.get_control_signal(sid)
            trials = segment_trials(loader, sid)

            anomalies = []

            # Check channel count
            if meta.n_channels != EXPECTED_CHANNELS:
                anomalies.append(f"Expected {EXPECTED_CHANNELS} channels, got {meta.n_channels}")

            # Check trial count
            if meta.n_trials != EXPECTED_TRIALS_PER_SUBJECT:
                anomalies.append(f"Expected {EXPECTED_TRIALS_PER_SUBJECT} trials, got {meta.n_trials}")

            # Check for CS=30 (termination marker)
            unique_cs = sorted(np.unique(cs).tolist())
            cs_30_count = int(np.sum(cs == CS_TERMINATION))
            if cs_30_count and (cs_30_count != 1 or cs[-1] != CS_TERMINATION):
                anomalies.append(f"ControlSignal contains value 30 (termination marker, {cs_30_count} samples)")

            # Direction distribution
            dir_counts = {}
            for t in trials:
                label = t.direction_label_8
                dir_counts[label] = dir_counts.get(label, 0) + 1

            # Check EOG for NaN/Inf (sample a few channels)
            eog = loader.get_eog(sid)
            nan_count = int(np.isnan(eog).sum())
            inf_count = int(np.isinf(eog).sum())
            if nan_count > 0:
                anomalies.append(f"{nan_count} NaN values in EOG")
            if inf_count > 0:
                anomalies.append(f"{inf_count} Inf values in EOG")

            # Channel statistics
            channel_stats = []
            for ch in range(min(meta.n_channels, 16)):
                row = eog[ch]
                channel_stats.append({
                    "channel": ch,
                    "min": round(float(np.min(row)), 2),
                    "max": round(float(np.max(row)), 2),
                    "mean": round(float(np.mean(row)), 2),
                    "std": round(float(np.std(row)), 2),
                })

            passed = not anomalies

            subjects_report.append({
                "subject_id": sid,
                "passed": passed,
                "n_channels": meta.n_channels,
                "n_samples": meta.n_samples,
                "n_trials": len(trials),
                "duration_sec": meta.duration_sec,
                "pd": meta.pd,
                "dist_screen": meta.dist_screen,
                "control_signal_values": unique_cs,
                "cs_30_count": cs_30_count,
                "nan_count": nan_count,
                "inf_count": inf_count,
                "anomalies": anomalies,
                "direction_distribution": dir_counts,
                "channel_stats": channel_stats,
            })
            total_anomalies.extend([(sid, a) for a in anomalies])

            # Release EOG to free memory
            loader.release_subject(sid)

        except Exception:
            logging.exception("Invalid dataset subject %s", sid)
            total_anomalies.append((sid, "Invalid subject schema or data"))
            subjects_report.append({
                "subject_id": sid,
                "passed": False,
                "anomalies": ["Invalid subject schema or data; inspect server logs"],
            })

    for sid in set(EXPECTED_SUBJECTS) - set(loader.subject_ids):
        subjects_report.append({"subject_id": sid, "passed": False, "anomalies": ["Expected subject is missing"]})
        total_anomalies.append((sid, "Expected subject is missing"))

    all_passed = all(s.get("passed", False) for s in subjects_report)

    return {
        "all_passed": all_passed,
        "n_subjects": len(loader.subject_ids),
        "total_anomalies": len(total_anomalies),
        "subjects": subjects_report,
    }
