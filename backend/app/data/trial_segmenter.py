"""
Trial Segmenter
================
Extracts trial boundaries and metadata from ControlSignal transitions.
Each trial consists of: outward saccade (CS=1) → return saccade (CS=2) → blink (CS=3).
"""
import numpy as np
from typing import List, Tuple
import logging

from app.core.config import (
    CS_OUTWARD, CS_RETURN, CS_BLINK, CS_TERMINATION, SAMPLING_RATE
)
from app.data.dataset_loader import DatasetLoader, TrialMetadata

logger = logging.getLogger(__name__)


def _find_segments(cs: np.ndarray, value: int) -> List[Tuple[int, int]]:
    """Find contiguous segments where cs == value.
    Returns list of (start_idx, end_idx_exclusive) tuples."""
    mask = (cs == value).astype(int)
    diff = np.diff(np.concatenate([[0], mask, [0]]))
    starts = np.where(diff == 1)[0]
    ends = np.where(diff == -1)[0]
    return list(zip(starts.tolist(), ends.tolist()))


def segment_trials(loader: DatasetLoader, subject_id: str) -> List[TrialMetadata]:
    """Extract all trials for a subject from ControlSignal transitions.

    Each trial is a triplet of consecutive (CS=1, CS=2, CS=3) segments.
    The CS=30 termination marker is excluded.

    Returns:
        List of TrialMetadata, one per trial (expected ~288).
    """
    cs = loader.get_control_signal(subject_id)
    tga = loader.get_target_ga_stream(subject_id)

    if tga.shape != (2, len(cs)) or loader.get_eog(subject_id).shape[1] != len(cs):
        raise ValueError("EOG/control/target sample counts or target shape mismatch")
    termination = np.flatnonzero(cs == CS_TERMINATION)
    if len(termination) and (len(termination) != 1 or termination[0] != len(cs) - 1):
        raise ValueError("Termination marker must occur once at the last sample")
    if not np.isin(cs, [CS_OUTWARD, CS_RETURN, CS_BLINK, CS_TERMINATION]).all():
        raise ValueError("Unexpected control value")
    valid_cs = cs[:-1] if len(termination) else cs
    runs = valid_cs[np.r_[True, np.diff(valid_cs) != 0]]
    if len(runs) % 3 or not np.array_equal(runs, np.tile([1, 2, 3], len(runs) // 3)):
        raise ValueError("Incomplete or misordered outward/return/blink sequence")

    # Find segments for each phase
    outward_segs = _find_segments(cs, CS_OUTWARD)
    return_segs = _find_segments(cs, CS_RETURN)
    blink_segs = _find_segments(cs, CS_BLINK)

    # Validate segment counts match
    n_out = len(outward_segs)
    n_ret = len(return_segs)
    n_blk = len(blink_segs)

    if n_out != n_ret or n_out != n_blk:
        logger.warning(
            f"{subject_id}: Segment count mismatch: "
            f"outward={n_out}, return={n_ret}, blink={n_blk}"
        )

    n_trials = min(n_out, n_ret, n_blk)
    trials = []

    for i in range(n_trials):
        o_start, o_end = outward_segs[i]
        r_start, r_end = return_segs[i]
        b_start, b_end = blink_segs[i]

        # Verify ordering: outward < return < blink
        if not (o_end == r_start and r_end == b_start):
            raise ValueError(f"Non-consecutive phases in trial {i}")

        # Target angles during the outward phase
        # Use the value at the start of the outward segment
        h_deg = float(tga[0, o_start])
        v_deg = float(tga[1, o_start])

        # Compute direction angle (0-360 degrees)
        angle_rad = np.arctan2(v_deg, h_deg)
        angle_deg = float(np.degrees(angle_rad))
        if angle_deg < 0:
            angle_deg += 360.0

        # Target magnitude
        magnitude = float(np.sqrt(h_deg**2 + v_deg**2))

        # Direction labels
        label_36 = _angle_to_bin(angle_deg, 36)
        label_8 = _angle_to_bin(angle_deg, 8)
        label_4 = _angle_to_bin(angle_deg, 4)

        trial = TrialMetadata(
            subject_id=subject_id,
            trial_id=i,
            outward_start=o_start,
            outward_end=o_end,
            return_start=r_start,
            return_end=r_end,
            blink_start=b_start,
            blink_end=b_end,
            target_horizontal_deg=round(h_deg, 6),
            target_vertical_deg=round(v_deg, 6),
            target_angle_deg=round(angle_deg, 2),
            target_magnitude_deg=round(magnitude, 6),
            direction_label_36=label_36,
            direction_label_8=label_8,
            direction_label_4=label_4,
        )
        trials.append(trial)

    logger.info(f"{subject_id}: Extracted {len(trials)} trials")
    return trials


def _angle_to_bin(angle_deg: float, n_bins: int) -> int:
    """Map an angle (0-360°) to a bin index using nearest-center assignment.

    Bins are evenly spaced starting at 0° with width = 360/n_bins.
    Bin centers: 0°, 360/n * 1, 360/n * 2, ...
    Each angle is assigned to the nearest bin center.

    Convention:
        n_bins=4:  Right(0), Up(1), Left(2), Down(3)
        n_bins=8:  Right(0), Up-Right(1), Up(2), Up-Left(3),
                   Left(4), Down-Left(5), Down(6), Down-Right(7)
        n_bins=36: Fine-grained direction index (0-35)
    """
    bin_width = 360.0 / n_bins
    # Shift angle so that bin 0 is centered at 0° (i.e., spans -half_width to +half_width)
    shifted = (angle_deg + bin_width / 2) % 360.0
    return int(shifted // bin_width)


def get_direction_label_name(label_index: int, n_classes: int) -> str:
    """Get human-readable direction label name."""
    if n_classes == 4:
        names = ["Right", "Up", "Left", "Down"]
    elif n_classes == 8:
        names = [
            "Right", "Up-Right", "Up", "Up-Left",
            "Left", "Down-Left", "Down", "Down-Right"
        ]
    elif n_classes == 36:
        return f"Dir_{label_index * 10}deg"
    else:
        return f"Class_{label_index}"
    return names[label_index % len(names)]


def get_trial_eog(
    loader: DatasetLoader,
    trial: TrialMetadata,
    phase: str = "outward",
    channels: List[int] = None,
) -> np.ndarray:
    """Extract EOG data for a specific trial phase.

    Args:
        loader: DatasetLoader instance
        trial: TrialMetadata for the trial
        phase: 'outward', 'return', 'blink', or 'full' (all phases)
        channels: Channel indices (0-based). None = all 16.

    Returns:
        EOG array of shape (n_channels, n_samples)
    """
    eog = loader.get_eog(trial.subject_id)

    if phase == "outward":
        start, end = trial.outward_start, trial.outward_end
    elif phase == "return":
        start, end = trial.return_start, trial.return_end
    elif phase == "blink":
        start, end = trial.blink_start, trial.blink_end
    elif phase == "full":
        start, end = trial.outward_start, trial.blink_end
    else:
        raise ValueError(f"Unknown phase: {phase}")

    if channels is not None:
        if not channels or len(set(channels)) != len(channels) or any(ch < 0 or ch >= eog.shape[0] for ch in channels):
            raise ValueError("Channels must be distinct valid zero-based indices")
        return eog[channels, start:end]
    return eog[:, start:end]
