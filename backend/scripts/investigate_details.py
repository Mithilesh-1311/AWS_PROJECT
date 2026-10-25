"""Detailed investigation of ControlSignal value 30 and target angle structure."""
import numpy as np
from scipy.io import loadmat
from pathlib import Path

ROOT = Path("c:/Users/Admin/OneDrive/Desktop/AWS project/Dataset_Isotropic/Dataset_Isotropic")

# 1. Where does value 30 occur?
print("=== ControlSignal Value 30 Investigation ===")
for sid in ["S1", "S2", "S3"]:
    cs = loadmat(str(ROOT / sid / "ControlSignal.mat"), squeeze_me=True)["ControlSignal"].flatten()
    idx30 = np.where(cs == 30)[0]
    print(f"{sid}: value 30 at indices {idx30[0]}..{idx30[-1]} (count={len(idx30)})")
    print(f"  Total samples: {len(cs)}")
    print(f"  Value before 30 region: cs[{max(0,idx30[0]-1)}]={cs[max(0,idx30[0]-1)]}")
    if idx30[-1]+1 < len(cs):
        print(f"  Value after 30 region: cs[{idx30[-1]+1}]={cs[idx30[-1]+1]}")
    # Check segment order
    transitions = np.where(np.diff(cs) != 0)[0]
    vals_at_transitions = [(int(t), int(cs[t]), int(cs[t+1])) for t in transitions[:10]]
    print(f"  First 10 transitions: {vals_at_transitions}")
    print()

# 2. Target angle structure
print("=== Target Angle Structure ===")
tga = loadmat(str(ROOT / "S1" / "Target_GA_stream.mat"), squeeze_me=True)["Target_GA_stream"]
print(f"Shape: {tga.shape}")
h_unique = np.unique(tga[0])
v_unique = np.unique(tga[1])
print(f"Horizontal unique values ({len(h_unique)}): {h_unique}")
print(f"Vertical unique values ({len(v_unique)}): {v_unique}")

# Compute direction angles from target pairs
cs = loadmat(str(ROOT / "S1" / "ControlSignal.mat"), squeeze_me=True)["ControlSignal"].flatten()

# Get outward saccade segments (value == 1)
mask = (cs == 1).astype(int)
starts = np.where(np.diff(np.concatenate([[0], mask])) == 1)[0]

directions = []
for s in starts:
    h = tga[0, s]
    v = tga[1, s]
    if h == 0.0 and v == 0.0:
        continue
    angle = np.degrees(np.arctan2(v, h))
    if angle < 0:
        angle += 360
    directions.append(round(angle, 2))

unique_dirs = sorted(set(directions))
print(f"\nUnique direction angles ({len(unique_dirs)}):")
for d in unique_dirs:
    count = directions.count(d)
    print(f"  {d:>8.2f} deg  (n={count})")

print(f"\nTotal outward saccade trials: {len(directions)}")

# Check trial phase durations
print("\n=== Trial Phase Durations (S1, first 5 trials) ===")
for phase_val in [1, 2, 3]:
    phase_mask = (cs == phase_val).astype(int)
    phase_starts = np.where(np.diff(np.concatenate([[0], phase_mask])) == 1)[0]
    phase_ends = np.where(np.diff(np.concatenate([phase_mask, [0]])) == -1)[0]
    durations = phase_ends[:5] - phase_starts[:5]
    dur_ms = durations / 256 * 1000
    print(f"Phase {phase_val}: first 5 durations (samples): {durations}")
    print(f"         first 5 durations (ms): {dur_ms.round(1)}")
