# Low-Latency EOG-Based Early Intent Detection for Eye Movements

> **Review 1 Milestone (~50% Completion Build)**  
> Academic Biomedical Signal Processing & Machine Learning Project  
> Validated on the University of Malta 16-Channel Isotropic EOG Dataset (14 Subjects, 4,032 Trials).

---

## 📌 Executive Overview

Traditional eye-gaze tracking and human-machine interfaces require a user to execute a complete saccadic movement and fixate on a target before detecting intention—introducing **200 to 400 milliseconds of latency**. 

This research project develops a **low-latency early intent detection pipeline** that decodes the intended saccadic direction within the first **20 ms to 100 ms** after saccade initiation from multi-channel Electrooculography (EOG).

```
   Visual Cue (CS=1)            Saccade Onset               Saccade Complete
          │                           │                            │
          │ ── Reaction: 150-250ms ── │ ── Duration: 40-60ms ───── │
          ├───────────────────────────┼─────────────┬──────────────┤
                                      ▲             ▲
                                      Window: 20ms  Window: 60ms
                                      (Early Intent Decoded Here)
```

---

## 🚀 Key Highlights & Accomplishments (Review 1)

- **Full Dataset Validation**: 100% structural verification of all 14 subjects (`S1`–`S14`), 4,032 experimental trials, 16 active monopolar channels at 256 Hz.
- **Biomedical Anomaly Discovery**: Uncovered and safely isolated the `CS=30` experimental termination marker.
- **Strict Causality Enforced**: Zero future data leakage; causal baseline centering; forward-only IIR drift filtering; exact sample ceiling conversion ($N = \lceil T_{ms} \cdot 256 / 1000 \rceil$).
- **Physiological Saccade Onset Detection**: Automated derivative thresholding with Median Absolute Deviation (MAD) noise estimation.
- **Verified Baseline ML**: Validated Logistic Regression & Linear SVM models on 8-class direction classification across 8 window durations (20ms to 200ms).
- **Interactive Research Dashboard**: Complete 8-page React + Vite + TypeScript web application with rich visualizations (Recharts, dynamic window slider, multi-channel waveforms).
- **Automated Test Suite**: 27 unit and integration tests covering signal processing, features, onset detection, window generation, and FastAPI endpoints.

---

## 🏗️ Project Architecture

```
AWS project/
├── Dataset_Isotropic/         # University of Malta raw .mat files (S1-S14)
├── backend/
│   ├── app/
│   │   ├── api/               # FastAPI route endpoints
│   │   ├── core/              # Global configuration & constants
│   │   ├── data/              # Lazy loader & trial segmenter
│   │   ├── signal_processing/ # Causal preprocessor & onset detector
│   │   ├── features/          # Early window & feature extractors
│   │   ├── models/            # Baseline classifiers
│   │   └── evaluation/        # Stratified cross-validation & metrics
│   ├── artifacts/             # Cached models, inspection reports, experiment JSONs
│   ├── scripts/               # CLI tools: inspect_dataset, run_baseline
│   ├── tests/                 # Comprehensive pytest suite (27 passing tests)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/             # 8 interactive dashboard pages
│   │   ├── services/          # Typed API client
│   │   └── hooks/             # Custom React hooks
│   ├── package.json
│   └── vite.config.ts
└── docs/
    ├── DATASET_REPORT.md      # Detailed dataset validation & anomaly report
    ├── METHODOLOGY.md         # Scientific & mathematical formulation
    ├── REVIEW_1_NOTES.md      # Presentation script & defense guide
    └── PHASE_2_PLAN.md        # Roadmap for deep learning & streaming
```

---

## ⚡ Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Run Backend API Server
```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 2. Run Interactive Research Frontend
```bash
cd frontend
npm install
npm run dev
```
- Dashboard: [http://localhost:5173](http://localhost:5173)

### 3. Run Automated Tests
```bash
cd backend
python -m pytest tests/ -v
```

### 4. Run Baseline Experiments via CLI
```bash
cd backend
python -m scripts.run_baseline --n-classes 8 --model logistic_regression --alignment onset
```

---

## 📊 Dashboard Pages

1. **Overview**: Project synopsis, core metrics, Review 1 progress status.
2. **Dataset Explorer**: Interactive viewer for 16-channel EOG waveforms, trial selector, and target direction compass.
3. **Signal Processing**: Raw vs. preprocessed signal comparator, first-derivative waveform, and detected saccade onset markers.
4. **Early Window Lab**: Interactive observation duration slider (20ms–200ms) with visual saccade cut markers.
5. **Experiments**: Accuracy vs. latency trade-off curve, confusion matrix, and classification metrics.
6. **Data Quality**: Automated multi-subject validation matrix, NaN/Inf checks, and anomaly reporting.
7. **Methodology**: Visual engineering pipeline and mathematical formulation.
8. **About**: Technical stack, project specifications, and Phase 2 roadmap.

---

## 📚 Academic Documentation

- [Comprehensive Project Analysis](docs/COMPREHENSIVE_PROJECT_ANALYSIS.md): In-depth, publication-grade report reference detailing biophysics, mathematics, dataset, ML models, and full architecture.
- [Dataset Report](docs/DATASET_REPORT.md): Complete data audit, electrode specifications, and ControlSignal analysis.
- [Methodology](docs/METHODOLOGY.md): Biophysical theory of EOG, spatial geometry, and causal processing.
- [Review Notes](docs/REVIEW_1_NOTES.md): Presentation walkthrough and defense Q&A guide.
- [Project Plan](docs/PHASE_2_PLAN.md): Deep temporal networks, continuous angular regression, and real-time streaming simulator.
