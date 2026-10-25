# Dataset card

Validated locally on 2026-10-26. Source: the supplied University of Malta Isotropic EOG archive and its accompanying PDF. This repository distributes code and derived experiment records; raw recordings remain excluded from Git.

| Field | Verified value |
|---|---|
| Cohort | S1 through S14; 14 subjects |
| Files | 70 MATLAB files, five per subject |
| EOG | 16 channels by approximately 299,821 samples; 256 Hz |
| Trials | 288 segmented trials per subject; 4,032 total |
| ControlSignal | Consecutive outward=1, return=2, blink=3; one final termination sample=30 |
| Targets | Horizontal/vertical target angles in degrees; 36 source directions mapped to eight 45-degree bins |
| PD / screen distance | Metres, as documented in the supplied PDF |
| Amplitude | Recorded units; voltage scaling is not established by the available documentation |
| Acquisition filters | PDF describes 30 Hz low-pass and 50 Hz notch filtering |

Discovery accepts a flat `S1/...` root or the supplied nested `Dataset_Isotropic/Dataset_Isotropic/` layout. Set `EOG_DATASET_ROOT` to override discovery. The loader validates file keys, dimensions, sample alignment and finite values. Segmentation rejects malformed phase order rather than inventing boundaries. The final 30 marker is expected and excluded. All 14 supplied subjects pass these checks.

Full-cohort SHA256 fingerprint: `e653e4f5c2b03fe40e0c057c17644f27a83fe7590d19510b2e4536f76aa952dc`. Per-file checksums are embedded in every published full-cohort manifest. Run `python -m scripts.verify_artifacts` from `backend` to compare the actual files with the published evidence.

At 100 ms, 3,610 trials have a confirmed onset and sufficient samples: 422 of 4,032 are excluded (89.53% coverage). The matched 400 ms comparison retains 3,596 trials (89.19%). Exclusions are saved per trial/window in local experiment directories. Accuracy is conditional on eligibility, not success across all cues. Rejected online trials abstain.

No redistribution or cloud-upload license was found in the supplied documentation. User permission to use the local recordings does not establish permission to publish them. Raw data has not been uploaded. Obtain and record the dataset owner's applicable license/permission before any S3 transfer. Do not infer clinical representativeness, free-head-motion robustness or external validity from this cohort.
