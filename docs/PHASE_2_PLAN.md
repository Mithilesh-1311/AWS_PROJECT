# Phase 2 Implementation Roadmap (Final 50%)

Following the successful completion of Review 1 (~50% milestone establishing data mastery, causal signal preprocessing, early window extraction, baseline ML, and interactive web dashboard), Phase 2 transitions from exploratory baselines to advanced deep architectures, subject-independent transfer learning, and real-time streaming validation.

---

## 1. Advanced Deep Learning Architectures

While Review 1 validated linear and regularized baselines (Logistic Regression, Linear SVM, Random Forests), Phase 2 will introduce neural architectures tailored for multi-channel physiological time-series:

### 1.1 1D Temporal Convolutional Networks (1D-TCN)
- **Rationale**: Dilated causal 1D convolutions capture multi-scale temporal dependencies without violating temporal causality.
- **Architecture**: Residual blocks with causal dilated convolutions, batch normalization, and dropout.
- **Advantage**: Superior gradient flow and significantly lower inference latency compared to recurrent architectures.

### 1.2 Spatial-Temporal Convolutional Networks (ST-CNN)
- **Rationale**: The 16 electrodes are spatially distributed in an isotropic ring around the eyes.
- **Layer 1 (Spatial Filter)**: $16 \times 1$ depthwise convolution across channels to learn virtual spatial bipolar derivations.
- **Layer 2 (Temporal Filter)**: $1 \times K$ temporal convolutions across the early observation window (e.g., 6 to 26 samples).

### 1.3 Lightweight Recurrent Architectures (GRU / LSTM)
- Benchmark against TCNs to evaluate sequence-to-one prediction efficiency under variable window lengths.

---

## 2. Continuous Angular Regression Formulation

In Phase 1, directions are binned into 8 discrete octants. In Phase 2, we formulate the task as continuous radial trajectory regression:
- Predict continuous angle $\hat{\theta} \in [0, 360^\circ)$.
- Target representation: Unit vector $(\sin \theta, \cos \theta)$.
- Loss Function: Negative Cosine Similarity Loss:
  $$\mathcal{L}_{angular} = 1 - (\hat{y}_h y_h + \hat{y}_v y_v)$$
- Evaluation Metric: Mean Absolute Angular Error (MAAE) in degrees.

---

## 3. Cross-Subject Generalization & Domain Adaptation

One of the largest hurdles in biomedical signal processing is inter-subject variability arising from:
- Differences in skull morphology and inter-pupillary distance (PD: 0.059m to 0.074m in dataset).
- Variations in skin-electrode contact impedance.
- Idiosyncratic saccade velocities and reaction latencies.

### Strategies:
1. **Leave-One-Subject-Out (LOSO) Cross-Validation**: Train on 13 subjects, evaluate on the 14th unseen subject.
2. **Covariance Alignment / Riemannian Alignment**: Align trial covariance matrices across subjects in Riemannian manifold space.
3. **Domain Adversarial Neural Networks (DANN)**: Train an adversarial feature extractor that maximizes direction classification accuracy while minimizing subject discriminator confidence.

---

## 4. Real-Time Streaming Simulation Pipeline

To validate practical clinical and assistive utility, Phase 2 will implement an asynchronous streaming testbed:
- **WebSocket Feed**: Feeds continuous EOG data sample-by-sample at 256 Hz.
- **Ring Buffer**: Fixed-length circular buffer holding the latest $N$ samples.
- **Causal Onset Engine**: Runs real-time derivative thresholding on every incoming sample.
- **Triggered Prediction**: The moment onset is flagged, the model triggers predictions at $t + 20$ms, $t + 40$ms, and $t + 60$ms.
- **Live Latency Profiler**: Measures wall-clock execution time per inference step (target: $< 2$ ms).

---

## 5. Timeline & Milestone Projections

```
Phase 2 Timeline:
Weeks 1–3:   Deep Learning Implementation (1D-TCN & Spatial-Temporal CNN)
Weeks 4–5:   Continuous Angle Regression & Loss Formulations
Weeks 6–7:   Cross-Subject Generalization & Domain Adaptation (LOSO)
Weeks 8–9:   WebSocket Streaming Testbed & End-to-End Latency Benchmarks
Weeks 10–12: Final Thesis Writing, Comparative Result Tables, Final Presentation
```
