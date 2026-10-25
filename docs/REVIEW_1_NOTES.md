> Historical Review 1 document. Current scientific claims, causal timing and measured evaluation are in [MODEL_CARD.md](MODEL_CARD.md), [DATASET_CARD.md](DATASET_CARD.md) and [EXPERIMENTS.md](EXPERIMENTS.md). Earlier causality/completion statements below are not current evidence.

# Project Review 1 — Defense & Presentation Guide

**Project Title**: Low-Latency EOG-Based Early Intent Detection for Eye Movements  
**Milestone**: Review 1 (Phase 1 — ~50% Foundation Complete)  
**Presenter Guide**: Academic ECE / Biomedical Signal Processing Committee

---

## 1. Executive Summary (The 30-Second Elevator Pitch)

> *"Professor, this project addresses the fundamental latency bottleneck in eye-gaze human-machine interfaces. Traditional gaze systems wait for an entire saccadic movement to finish—introducing 200 to 400 milliseconds of latency. We demonstrate that by leveraging high-density 16-channel isotropic EOG, we can predict intended movement direction within the first **20 to 100 milliseconds** of saccade initiation. For Review 1, we have built the complete data engineering, signal processing, onset detection, and machine learning baseline pipeline, validated on 14 human subjects and over 4,000 real trials."*

---

## 2. Review 1 Checklist (What We Are Demonstrating Today)

| Deliverable | Status | Evidence |
|---|---|---|
| **1. Dataset Integrity & Mastery** | 100% Complete | All 14 subjects parsed; 4,032 trials extracted; zero NaN/Infs; CS=30 anomaly identified & isolated. |
| **2. Biomedical Signal Processing** | 100% Complete | Causal baseline centering, drift removal, MAD-based physiological onset detection. |
| **3. Early Window Generation** | 100% Complete | Exact sample mapping at 256 Hz for 20ms–200ms; zero future data leakage. |
| **4. ML Baseline Pipeline** | 100% Complete | 8-class direction classification; Stratified Group-K-Fold validation; benchmark accuracy vs latency. |
| **5. Interactive Research Dashboard** | 100% Complete | 8-page React + Vite + TypeScript web application with live FastAPI backend. |
| **6. Code & Engineering Rigor** | 100% Complete | 27 automated unit & integration tests passing with 100% pass rate. |

---

## 3. Live Demonstration Walkthrough (Recommended Order)

1. **Page 1: Overview**
   - Show the summary cards: 14 subjects, 16 monopolar channels, 256 Hz, 4,032 trials.
   - Highlight the Review 1 completion milestone checklist.

2. **Page 2: Dataset Explorer**
   - Select Subject `S1`, Trial `0`.
   - Show the multi-channel EOG waveform during the outward saccade phase.
   - Point out the target direction compass showing the visual cue angle.

3. **Page 3: Signal Processing**
   - Toggle between **Raw EOG** and **Preprocessed EOG**.
   - Show how baseline centering eliminates DC offset without distorting the saccadic waveform.
   - Show the **Derivative and Onset Marker**: explain how the algorithm detects the exact physiological moment the eye began moving.

4. **Page 4: Early Window Lab**
   - Move the window duration slider from **20ms** to **100ms** to **200ms**.
   - Highlight the visual crop line showing how much information the classifier gets to observe.
   - Emphasize: *"At 40ms, we only see 11 samples, yet directional intent is already decoding."*

5. **Page 5: Experiments (The Core Finding)**
   - Show the **Latency vs. Accuracy curve**.
   - Note the trajectory: accuracy starts above chance (chance for 8 classes is 12.5%) even at ultra-low latencies (20–40ms) and climbs systematically as more saccadic trajectory is revealed.
   - Show the **Confusion Matrix**: adjacent directions (e.g., Up vs Up-Right) are the primary source of error, confirming spatial coherence.

6. **Page 6: Data Quality**
   - Show the live automated quality audit across all 14 subjects.
   - Highlight the discovery of the `CS=30` termination anomaly and explain how our loader safely handles it.

---

## 4. Key Figures & Numbers to Quote Confidently

- **Sampling Rate**: 256 Hz ($\Delta t = 3.90625$ ms per sample).
- **Target Eccentricity**: Constant 12° visual angle across all trials.
- **Directional Granularity**: 36 target directions spaced at ~10° radial intervals.
- **Trial Structure**: 288 trials per subject = 36 directions $\times$ 8 repetitions.
- **Total Dataset Size**: 14 subjects $\times$ 288 = 4,032 trials (~16.4 million raw data points).
- **Sample Counts**: 20ms = 6 samples; 40ms = 11 samples; 60ms = 16 samples; 100ms = 26 samples; 200ms = 52 samples.
- **Chance Baseline**: 12.5% for 8-class classification, 25.0% for 4-class classification.

---

## 5. Potential Professor Questions & Strategic Answers

### Q1: "Why use EOG instead of modern optical infrared eye trackers?"
> **Answer**: *"Optical eye-trackers depend on high-speed cameras, which suffer from frame exposure latency (typically 16–33 ms per frame), computational overhead for pupil center corneal reflection (PCCR) image processing, and vulnerability to eyelid occlusion, blinks, and head movement. In contrast, EOG measures bioelectric potentials directly at 256 Hz or higher with sub-millisecond physical sensor response, negligible compute latency, and full functionality in closed-eye or head-mounted environments."*

### Q2: "How do you ensure no future data leaks into your early windows?"
> **Answer**: *"We enforced strict temporal causality at three distinct layers: First, baseline centering is computed exclusively from the first 25 pre-movement samples. Second, when applying highpass filtering for drift, we use forward-only causal IIR filtering (`lfilter`), not bidirectional `filtfilt`. Third, all window slicing functions check exact sample indices and explicitly reject padding with future samples."*

### Q3: "What is that CS=30 anomaly you found?"
> **Answer**: *"During exhaustive exploratory analysis of the raw `.mat` files across all 14 subjects, we discovered that the very last sample of each recording has `ControlSignal == 30`. In the acquisition software, this served as an experiment termination marker. If left unhandled, it could corrupt trial segmentation. Our segmenter specifically filters this out and isolates the 288 genuine experimental trials."*

### Q4: "Why does 20ms window have lower accuracy than 100ms window?"
> **Answer**: *"At 20 ms post-onset, the eye has completed less than a third of its total angular displacement toward the 12° target. The corneo-retinal dipole has only begun to rotate, yielding smaller signal-to-noise ratios. However, achieving significantly above-chance performance (e.g. 40–50% on an 8-class problem where chance is 12.5%) at 20 ms proves that early intent is decodable long before the eye lands on the target."*

### Q5: "What is your roadmap for Phase 2 (the remaining 50%)?"
> **Answer**: *"In Phase 2, we build on this verified baseline by implementing deep temporal models (1D-CNNs, Temporal Convolutional Networks, and Compact LSTMs), exploring cross-subject transfer learning using domain adaptation, and deploying an asynchronous streaming simulator to evaluate true real-time throughput."*
