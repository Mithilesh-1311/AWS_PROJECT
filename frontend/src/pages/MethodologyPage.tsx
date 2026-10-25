export default function MethodologyPage() {
  return (
    <div>
      {/* Pipeline */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-title" style={{ marginBottom: 16, textAlign: 'center' }}>Processing Pipeline</div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
          {[
            { step: 'University of Malta EOG Dataset', desc: '14 subjects, 16 channels, 256 Hz' },
            { step: 'Trial Segmentation', desc: 'ControlSignal-based: outward (CS=1), return (CS=2), blink (CS=3)' },
            { step: 'Saccade Onset Detection', desc: 'Derivative thresholding with MAD noise estimation' },
            { step: 'Partial Observation Windows', desc: '20ms → 200ms with proper ms-to-sample conversion' },
            { step: 'Feature Extraction', desc: '13 per-channel features × 16 channels + cross-channel' },
            { step: 'Baseline Classifier', desc: 'Logistic Regression with subject-level train/test split' },
            { step: 'Accuracy vs. Latency Evaluation', desc: 'Per-window metrics, confusion matrices, F1 scores' },
          ].map((item, i) => (
            <div key={i}>
              <div className="pipeline-step" style={{ minWidth: 400, justifyContent: 'space-between' }}>
                <strong style={{ color: 'var(--accent)' }}>{item.step}</strong>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 12 }}>{item.desc}</span>
              </div>
              {i < 6 && <div style={{ textAlign: 'center', color: 'var(--accent)', fontSize: 18 }}>↓</div>}
            </div>
          ))}
        </div>
      </div>

      {/* Key concepts */}
      <div className="grid-2">
        <div className="card">
          <div className="card-title" style={{ marginBottom: 12 }}>Core Pipeline & Baseline Architecture</div>
          <ul style={{ color: 'var(--text-secondary)', fontSize: 13, paddingLeft: 20, lineHeight: 2 }}>
            <li>Dataset validation and structural inspection</li>
            <li>EOG waveform visualization across all 16 channels</li>
            <li>ControlSignal-based trial segmentation (288 trials/subject)</li>
            <li>Saccade onset detection (derivative + MAD thresholding)</li>
            <li>Partial observation windows (20ms–200ms)</li>
            <li>Lightweight feature extraction (13 features × 16 channels)</li>
            <li>Baseline Logistic Regression classifier</li>
            <li>Subject-level stratified train/test split</li>
            <li>8-class direction prediction (45° bins)</li>
            <li>Latency-vs-accuracy analysis</li>
          </ul>
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 12 }}>Advanced Extensions & Deep Architectures</div>
          <ul style={{ color: 'var(--text-muted)', fontSize: 13, paddingLeft: 20, lineHeight: 2 }}>
            <li>LSTM/GRU sequential temporal models</li>
            <li>Spatial-Temporal 1D CNN architectures</li>
            <li>Adaptive confidence-based early stopping</li>
            <li>Leave-One-Subject-Out cross-validation</li>
            <li>Electrode subset optimization</li>
            <li>Subject personalization / domain adaptation</li>
            <li>Continuous radial angle regression</li>
            <li>Robustness and generalization studies</li>
            <li>Real-time causal streaming verification</li>
            <li>High-throughput assistive interface integration</li>
          </ul>
        </div>
      </div>

      {/* Technical notes */}
      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title" style={{ marginBottom: 12 }}>Important Technical Distinctions</div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
          <p><strong style={{ color: 'var(--accent)' }}>Cue Onset vs. Saccade Onset:</strong> The ControlSignal marks when the visual
            cue appears (CS=1). The actual eye movement begins ~150–250ms later due to human reaction time.
            Our onset detector estimates the physiological onset of the saccade from the EOG derivative signal.</p>
          <p style={{ marginTop: 12 }}><strong style={{ color: 'var(--accent)' }}>Early Intent Detection:</strong> This term refers to
            early directional classification using the initial portion of an ongoing saccadic EOG transition.
            It does <em>not</em> mean predicting intention before the eye begins to move.</p>
          <p style={{ marginTop: 12 }}><strong style={{ color: 'var(--accent)' }}>Causal vs. Non-Causal Processing:</strong> Zero-phase
            filtering (filtfilt) uses both past and future samples — it is non-causal and cannot be claimed as
            real-time compatible. Our baseline uses only causal preprocessing for the latency experiment.</p>
          <p style={{ marginTop: 12 }}><strong style={{ color: 'var(--accent)' }}>Data Leakage Prevention:</strong> Feature normalization
            is fitted on training data only. All windows from the same trial remain in the same split. Subject-level
            splitting prevents within-subject correlation from inflating cross-subject results.</p>
        </div>
      </div>
    </div>
  );
}
