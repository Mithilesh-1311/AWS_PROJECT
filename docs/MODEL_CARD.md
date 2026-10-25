# Model card

Intended use: recorded-data research into early eight-direction EOG classification. This is a cue-triggered demonstration, not a medical device, a validated assistive controller or pre-movement intention detection.

The active serving model is logistic regression at a predeclared 100 ms budget, with a training-fitted StandardScaler and 212 ordered `physical-v2` features from all 16 channels. Outer evaluation is leave-one-subject-out over all 14 subjects. In each outer fold, a training subject selects C from {0.1, 1.0} by balanced accuracy; the selected setting is refitted on all outer training subjects. No outer subject enters selection. The final model repeats selection within the full cohort, then refits all eligible trials; the final selected C is 0.1. Demo predictions on this cohort therefore do not constitute additional held-out evaluation.

| Final runtime evaluation | Result |
|---|---|
| Experiment | `46c8ad758f244c698eaceb90f161219a` |
| Runtime | scikit-learn 1.5.2; exact numerical dependencies in manifest |
| Eligible predictions / source trials | 3,610 / 4,032; 89.53% |
| Accuracy | 77.8393% |
| Macro F1 | 0.779398 |
| Subject-bootstrap mean-accuracy interval | 71.91% to 82.15%; 2,000 resamples, seed 42 |
| Serving ID | `46c8ad758f244c698eaceb90f161219a_logistic_100` |

The interval describes subject-mean accuracy, whereas the headline is pooled trial accuracy. With only 14 subjects it is not an external-validation interval. Confusion matrices, class support, precision/recall/F1, balanced accuracy, subject splits and predictions are in `backend/published/46c8ad758f244c698eaceb90f161219a.json`.

The causal processor waits for the first 25 cue samples: 97.65625 ms sample budget. Quietness of that interval is not guaranteed. A first-order 0.1 Hz high-pass filter carries its state; the channel set is fixed. Three consecutive threshold exceedances confirm onset, two samples after its estimated crossing. Crossings after sample 200 are rejected; the timing-reliability flag is heuristic. No fallback onset is used. Thresholds, filtered prefixes and decision windows do not depend on later samples. Samples preceding calibration completion are intentionally unavailable for an early decision.

At 256 Hz, a 100 ms request takes 26 samples: 101.5625 ms sample budget, 97.65625 ms span. Readiness is the latest of calibration completion, onset confirmation and the end of the observation window. S1/trial 0 becomes ready at sample 82, 320.3125 ms after cue. This is separate from computer inference time and playback scheduling.

Warm local benchmark, S1 trials 0..19, one warm-up, 20 predictions: median feature compute 4.16 ms, model compute 0.354 ms, causal processing plus inference 11.37 ms, HTTP round trip 29.44 ms. P95 HTTP was 33.35 ms. These measurements exclude physical acquisition and internet delay and can vary with hardware/load/cache. Definitions and raw summary are in `results/serving_benchmark.json`; server processing starts after loading the trial, while HTTP time includes that loading/serialization overhead.

Outputs are uncalibrated class probabilities, not confidence guarantees. Model loading requires the exact scikit-learn version, preprocessing/feature schema, class order and artifact checksum. Only trusted project-produced joblib files may enter artifact storage; a checksum does not make an untrusted pickle safe. Missing/incompatible models fail explicitly. Absent confirmed windows abstain.

The 4,880-parameter causal TCN reached 76.2327% accuracy and 0.762474 macro F1 on the same 3,610 eligible trials with 14-subject LOSO. Inner validation selected epochs before refitting each outer training set. It did not replace logistic serving. No clinical, independent-site, connected-hardware or calibrated-confidence validation has been performed.
