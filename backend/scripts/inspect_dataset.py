"""
Dataset Inspection Script
=========================
Inspects all .mat files across all 14 subjects in the University of Malta
EOG Isotropic dataset. Generates a comprehensive JSON validation report.
"""

import os
import sys
import json
import numpy as np
from scipy.io import loadmat
from pathlib import Path
from datetime import datetime

DATASET_ROOT = Path(__file__).resolve().parents[2] / "data" / "Dataset_Isotropic"
REPORT_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "reports"

EXPECTED_FILES = ["EOG.mat", "ControlSignal.mat", "Target_GA_stream.mat", "PD.mat", "Dist_screen.mat"]
EXPECTED_SUBJECTS = [f"S{i}" for i in range(1, 15)]
SAMPLING_RATE = 256  # Hz


def safe_stats(arr):
    """Compute stats, handling NaN/Inf."""
    flat = arr.flatten().astype(float)
    return {
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
        "min": float(np.nanmin(flat)) if flat.size > 0 else None,
        "max": float(np.nanmax(flat)) if flat.size > 0 else None,
        "mean": float(np.nanmean(flat)) if flat.size > 0 else None,
        "std": float(np.nanstd(flat)) if flat.size > 0 else None,
        "nan_count": int(np.isnan(flat).sum()),
        "inf_count": int(np.isinf(flat).sum()),
        "size": int(flat.size),
    }


def inspect_mat(filepath):
    """Load and inspect a single .mat file."""
    try:
        data = loadmat(str(filepath), squeeze_me=False)
    except Exception as e:
        return {"error": str(e), "keys": []}
    
    # Filter out MATLAB metadata keys
    user_keys = [k for k in data.keys() if not k.startswith("__")]
    result = {"keys": user_keys, "variables": {}}
    
    for key in user_keys:
        val = data[key]
        if isinstance(val, np.ndarray):
            info = safe_stats(val)
            # For small arrays, include actual values
            if val.size <= 100:
                try:
                    info["values"] = val.tolist()
                except:
                    info["values"] = "non-serializable"
            # Unique values for small cardinality
            unique = np.unique(val[~np.isnan(val)]) if np.issubdtype(val.dtype, np.floating) else np.unique(val)
            if len(unique) <= 200:
                info["unique_values"] = unique.tolist()
                info["unique_count"] = len(unique)
            else:
                info["unique_count"] = len(unique)
            result["variables"][key] = info
        else:
            result["variables"][key] = {"type": str(type(val)), "value": str(val)[:200]}
    
    return result


def inspect_subject(subject_id, dataset_root):
    """Inspect all files for a single subject."""
    subject_dir = dataset_root / subject_id
    report = {
        "subject_id": subject_id,
        "exists": subject_dir.exists(),
        "files": {},
        "missing_files": [],
        "anomalies": [],
        "validation_passed": True,
    }
    
    if not subject_dir.exists():
        report["validation_passed"] = False
        report["anomalies"].append(f"Subject directory not found: {subject_dir}")
        return report
    
    # Check for expected files
    for fname in EXPECTED_FILES:
        fpath = subject_dir / fname
        if not fpath.exists():
            report["missing_files"].append(fname)
            report["anomalies"].append(f"Missing file: {fname}")
            report["validation_passed"] = False
        else:
            report["files"][fname] = inspect_mat(fpath)
            report["files"][fname]["file_size_bytes"] = fpath.stat().st_size
    
    # Check for unexpected files
    actual_files = [f.name for f in subject_dir.iterdir() if f.is_file()]
    unexpected = set(actual_files) - set(EXPECTED_FILES)
    if unexpected:
        report["anomalies"].append(f"Unexpected files: {list(unexpected)}")
    
    # --- Specific validations ---
    
    # EOG shape check
    if "EOG.mat" in report["files"] and "error" not in report["files"]["EOG.mat"]:
        eog_vars = report["files"]["EOG.mat"]["variables"]
        for key, info in eog_vars.items():
            shape = info.get("shape", [])
            if len(shape) == 2:
                channels, samples = shape
                report["eog_channels"] = channels
                report["eog_samples"] = samples
                report["eog_duration_sec"] = round(samples / SAMPLING_RATE, 2)
                report["eog_variable_name"] = key
                if channels != 16:
                    report["anomalies"].append(f"EOG channels = {channels}, expected 16")
                if info["nan_count"] > 0:
                    report["anomalies"].append(f"EOG has {info['nan_count']} NaN values")
                if info["inf_count"] > 0:
                    report["anomalies"].append(f"EOG has {info['inf_count']} Inf values")
                # Per-channel stats
                break
    
    # ControlSignal check
    if "ControlSignal.mat" in report["files"] and "error" not in report["files"]["ControlSignal.mat"]:
        cs_vars = report["files"]["ControlSignal.mat"]["variables"]
        for key, info in cs_vars.items():
            report["control_signal_variable_name"] = key
            unique = info.get("unique_values", [])
            report["control_signal_unique_values"] = unique
            # Check for anomalous value 30
            if 30 in unique or 30.0 in unique:
                report["anomalies"].append(f"ControlSignal contains value 30 (not documented as 1,2,3)")
            expected_vals = {0, 1, 2, 3}
            unexpected_vals = set(unique) - expected_vals - {30, 30.0}
            if unexpected_vals:
                report["anomalies"].append(f"ControlSignal unexpected values: {list(unexpected_vals)}")
            break
    
    # Target_GA_stream check
    if "Target_GA_stream.mat" in report["files"] and "error" not in report["files"]["Target_GA_stream.mat"]:
        tga_vars = report["files"]["Target_GA_stream.mat"]["variables"]
        for key, info in tga_vars.items():
            shape = info.get("shape", [])
            if len(shape) == 2:
                report["target_ga_shape"] = shape
                report["target_ga_variable_name"] = key
                if shape[0] != 2:
                    report["anomalies"].append(f"Target_GA_stream rows = {shape[0]}, expected 2")
                break
    
    # PD check
    if "PD.mat" in report["files"] and "error" not in report["files"]["PD.mat"]:
        pd_vars = report["files"]["PD.mat"]["variables"]
        for key, info in pd_vars.items():
            if info.get("values") is not None:
                report["pd_value"] = info["values"]
                report["pd_variable_name"] = key
            break
    
    # Dist_screen check
    if "Dist_screen.mat" in report["files"] and "error" not in report["files"]["Dist_screen.mat"]:
        ds_vars = report["files"]["Dist_screen.mat"]["variables"]
        for key, info in ds_vars.items():
            if info.get("values") is not None:
                report["dist_screen_value"] = info["values"]
                report["dist_screen_variable_name"] = key
            break
    
    # Signal length alignment
    eog_samples = report.get("eog_samples")
    tga_shape = report.get("target_ga_shape")
    if eog_samples and tga_shape:
        tga_samples = tga_shape[1]
        if eog_samples != tga_samples:
            report["anomalies"].append(
                f"EOG samples ({eog_samples}) != Target_GA_stream samples ({tga_samples})"
            )
    
    cs_vars = report["files"].get("ControlSignal.mat", {}).get("variables", {})
    for key, info in cs_vars.items():
        cs_shape = info.get("shape", [])
        if len(cs_shape) >= 1:
            cs_samples = cs_shape[-1] if len(cs_shape) == 2 else cs_shape[0]
            if eog_samples and cs_samples != eog_samples:
                report["anomalies"].append(
                    f"ControlSignal samples ({cs_samples}) != EOG samples ({eog_samples})"
                )
        break
    
    return report


def compute_per_channel_stats(dataset_root, subject_id):
    """Compute per-channel EOG statistics for a subject."""
    mat = loadmat(str(dataset_root / subject_id / "EOG.mat"), squeeze_me=False)
    user_keys = [k for k in mat.keys() if not k.startswith("__")]
    eog = mat[user_keys[0]]
    
    channel_stats = []
    for ch in range(eog.shape[0]):
        row = eog[ch, :]
        channel_stats.append({
            "channel": ch + 1,
            "min": float(np.nanmin(row)),
            "max": float(np.nanmax(row)),
            "mean": float(np.nanmean(row)),
            "std": float(np.nanstd(row)),
            "nan_count": int(np.isnan(row).sum()),
            "inf_count": int(np.isinf(row).sum()),
        })
    return channel_stats


def count_trials_from_control(dataset_root, subject_id):
    """Count trial segments from ControlSignal transitions."""
    mat = loadmat(str(dataset_root / subject_id / "ControlSignal.mat"), squeeze_me=True)
    user_keys = [k for k in mat.keys() if not k.startswith("__")]
    cs = mat[user_keys[0]].flatten()
    
    # Detect transitions (changes in control signal value)
    diff = np.diff(cs)
    transitions = np.where(diff != 0)[0]
    
    # Count segments for each unique value
    unique_vals = np.unique(cs)
    segment_counts = {}
    for v in unique_vals:
        # Find contiguous regions of this value
        mask = (cs == v).astype(int)
        starts = np.where(np.diff(np.concatenate([[0], mask])) == 1)[0]
        segment_counts[int(v)] = len(starts)
    
    return {
        "unique_values": unique_vals.tolist(),
        "total_transitions": len(transitions),
        "segments_per_value": segment_counts,
        "signal_length": len(cs),
    }


def main():
    # Try alternate dataset paths
    dataset_root = DATASET_ROOT
    if not dataset_root.exists():
        alt = Path(__file__).resolve().parents[2] / "Dataset_Isotropic" / "Dataset_Isotropic"
        if alt.exists():
            dataset_root = alt
        else:
            alt2 = Path("c:/Users/Admin/OneDrive/Desktop/AWS project/Dataset_Isotropic/Dataset_Isotropic")
            if alt2.exists():
                dataset_root = alt2
            else:
                print(f"ERROR: Dataset not found at {DATASET_ROOT}")
                sys.exit(1)
    
    print(f"Dataset root: {dataset_root}")
    print(f"Inspecting {len(EXPECTED_SUBJECTS)} subjects...\n")
    
    full_report = {
        "generated_at": datetime.now().isoformat(),
        "dataset_root": str(dataset_root),
        "expected_subjects": EXPECTED_SUBJECTS,
        "sampling_rate_hz": SAMPLING_RATE,
        "subjects": {},
        "summary": {},
    }
    
    all_passed = True
    total_anomalies = []
    
    for sid in EXPECTED_SUBJECTS:
        print(f"  Inspecting {sid}...")
        report = inspect_subject(sid, dataset_root)
        
        # Add per-channel stats
        try:
            report["eog_channel_stats"] = compute_per_channel_stats(dataset_root, sid)
        except Exception as e:
            report["anomalies"].append(f"Failed to compute per-channel stats: {e}")
        
        # Add trial count info
        try:
            report["trial_info"] = count_trials_from_control(dataset_root, sid)
        except Exception as e:
            report["anomalies"].append(f"Failed to count trials: {e}")
        
        full_report["subjects"][sid] = report
        
        if not report["validation_passed"]:
            all_passed = False
        if report["anomalies"]:
            total_anomalies.extend([(sid, a) for a in report["anomalies"]])
        
        # Print summary line
        status = "PASS" if report["validation_passed"] else "FAIL"
        n_anom = len(report["anomalies"])
        eog_shape = f"{report.get('eog_channels', '?')}x{report.get('eog_samples', '?')}"
        print(f"    [{status}] EOG={eog_shape}, anomalies={n_anom}")
    
    # Summary
    full_report["summary"] = {
        "all_passed": all_passed,
        "subjects_inspected": len(EXPECTED_SUBJECTS),
        "total_anomalies": len(total_anomalies),
        "anomaly_list": [{"subject": s, "message": m} for s, m in total_anomalies],
    }
    
    print(f"\n{'='*60}")
    print(f"  Overall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    print(f"  Total anomalies: {len(total_anomalies)}")
    for s, m in total_anomalies:
        print(f"    [{s}] {m}")
    print(f"{'='*60}")
    
    # Save report
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "dataset_inspection_report.json"
    with open(report_path, "w") as f:
        json.dump(full_report, f, indent=2, default=str)
    print(f"\nReport saved to: {report_path}")
    
    return full_report


if __name__ == "__main__":
    main()
