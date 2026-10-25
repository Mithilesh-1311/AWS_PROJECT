# Dataset Validation Report

**Generated**: 2026-09-15  
**Dataset**: University of Malta EOG Isotropic Dataset  
**Source**: `Dataset_Isotropic/Dataset_Isotropic/`

---

## Summary

| Property | Value |
|---|---|
| Subjects | 14 (S1–S14) |
| Files per subject | 5 (EOG.mat, ControlSignal.mat, Target_GA_stream.mat, PD.mat, Dist_screen.mat) |
| EOG channels | 16 monopolar |
| Sampling rate | 256 Hz |
| Samples per subject | ~299,821 (range: 299,819–299,825) |
| Recording duration | ~1,171 seconds (~19.5 minutes) per subject |
| Trials per subject | 288 |
| Total trials | 4,032 |
| Target directions | 36 (≈10° spacing) |
| Trials per direction | 8 per subject |
| Target magnitude | 12° |
| Acquisition filters | 30 Hz low-pass, 50 Hz notch |

## Validation Status

| Subject | EOG Shape | CS Values | Trials | PD (m) | Dist (m) | NaN | Inf | Status |
|---|---|---|---|---|---|---|---|---|
| S1 | 16×299,821 | {1,2,3,30} | 288 | 0.067 | 0.56 | 0 | 0 | ✓ PASS |
| S2 | 16×299,822 | {1,2,3,30} | 288 | 0.0665 | 0.54 | 0 | 0 | ✓ PASS |
| S3 | 16×299,821 | {1,2,3,30} | 288 | 0.064 | 0.55 | 0 | 0 | ✓ PASS |
| S4 | 16×299,822 | {1,2,3,30} | 288 | 0.074 | 0.545 | 0 | 0 | ✓ PASS |
| S5 | 16×299,822 | {1,2,3,30} | 288 | 0.062 | 0.547 | 0 | 0 | ✓ PASS |
| S6 | 16×299,821 | {1,2,3,30} | 288 | 0.064 | 0.55 | 0 | 0 | ✓ PASS |
| S7 | 16×299,821 | {1,2,3,30} | 288 | 0.065 | 0.545 | 0 | 0 | ✓ PASS |
| S8 | 16×299,825 | {1,2,3,30} | 288 | 0.06 | 0.535 | 0 | 0 | ✓ PASS |
| S9 | 16×299,822 | {1,2,3,30} | 288 | 0.064 | 0.545 | 0 | 0 | ✓ PASS |
| S10 | 16×299,822 | {1,2,3,30} | 288 | 0.063 | 0.55 | 0 | 0 | ✓ PASS |
| S11 | 16×299,819 | {1,2,3,30} | 288 | 0.061 | 0.545 | 0 | 0 | ✓ PASS |
| S12 | 16×299,822 | {1,2,3,30} | 288 | 0.06 | 0.55 | 0 | 0 | ✓ PASS |
| S13 | 16×299,821 | {1,2,3,30} | 288 | 0.059 | 0.545 | 0 | 0 | ✓ PASS |
| S14 | 16×299,821 | {1,2,3,30} | 288 | 0.062 | 0.545 | 0 | 0 | ✓ PASS |

**Result: ALL 14 SUBJECTS PASSED STRUCTURAL VALIDATION**

## ControlSignal Structure

The ControlSignal contains values **1, 2, 3, and 30**.

### Phase Mapping
| Value | Phase | Duration (samples) | Duration (ms) | Description |
|---|---|---|---|---|
| 1 | Outward saccade | ~260 | ~1,016 | Centre → target gaze shift |
| 2 | Return saccade | ~259 | ~1,012 | Target → centre return |
| 3 | Blink period | ~520 | ~2,031 | Relaxation / blink interval |
| **30** | **Termination** | **1** | **3.9** | **Single sample at recording end** |

### Anomaly: Value 30
- **Location**: Always the **very last sample** of each subject's recording.
- **Count**: Exactly 1 sample per subject (14 total).
- **Interpretation**: Recording termination marker, NOT an experimental condition.
- **Handling**: Excluded from trial segmentation. Logged but not treated as a trial phase.

### Trial Sequence
Trials follow the repeating pattern: `1 → 2 → 3 → 1 → 2 → 3 → ... → 30`

## Target Direction Structure

### Coordinate System
- `Target_GA_stream` row 1 = horizontal gaze angle (degrees)
- `Target_GA_stream` row 2 = vertical gaze angle (degrees)
- Direction computed as: `θ = atan2(vertical, horizontal)`, normalized to 0°–360°

### 36 Directions
Directions are NOT equally spaced at exactly 10°. The angular values follow:

| # | Angle (°) | Trials/Subject |
|---|---|---|
| 1 | 0.00 | 8 |
| 2 | 10.14 | 8 |
| 3 | 20.21 | 8 |
| 4 | 30.18 | 8 |
| 5 | 40.07 | 8 |
| 6 | 49.93 | 8 |
| 7 | 59.82 | 8 |
| 8 | 69.79 | 8 |
| 9 | 79.86 | 8 |
| 10 | 90.00 | 8 |
| 11 | 100.14 | 8 |
| 12 | 110.21 | 8 |
| 13 | 120.18 | 8 |
| 14 | 130.07 | 8 |
| 15 | 139.93 | 8 |
| 16 | 149.82 | 8 |
| 17 | 159.79 | 8 |
| 18 | 169.86 | 8 |
| 19 | 180.00 | 8 |
| 20 | 190.14 | 8 |
| 21 | 200.21 | 8 |
| 22 | 210.18 | 8 |
| 23 | 220.07 | 8 |
| 24 | 229.93 | 8 |
| 25 | 239.82 | 8 |
| 26 | 249.79 | 8 |
| 27 | 259.86 | 8 |
| 28 | 270.00 | 8 |
| 29 | 280.14 | 8 |
| 30 | 290.21 | 8 |
| 31 | 300.18 | 8 |
| 32 | 310.07 | 8 |
| 33 | 319.93 | 8 |
| 34 | 329.82 | 8 |
| 35 | 339.79 | 8 |
| 36 | 349.86 | 8 |

**Distribution: Perfectly balanced** — 8 trials per direction per subject.

### Coordinate Values
- Horizontal range: [-12.0, 12.0] degrees (19 unique values)
- Vertical range: [-12.0, 12.0] degrees (19 unique values)
- Target magnitude: consistently 12° (verified by √(h² + v²) ≈ 12.0 for all non-zero targets)

## Signal Quality

- **No NaN values** in any subject's EOG data.
- **No Inf values** in any subject's EOG data.
- EOG voltage range varies by subject (typical: -5000 to +3000 µV range).
- All signals are float64.
- Signal lengths are aligned: EOG, ControlSignal, and Target_GA_stream have matching sample counts per subject.

## Known Limitations

1. The exact electrode montage positions are not embedded in the .mat files (documented in DataDescription.pdf).
2. Channel labels are indexed 1–16 without semantic names in the data files.
3. The ControlSignal timing may not exactly mark physiological saccade onset — there is likely a human reaction delay after the cue appears.
