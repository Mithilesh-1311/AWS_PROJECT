export default function AboutPage() {
  const completed = [
    'Dataset parsing and structural validation',
    'All 14 subjects readable with 288 trials each',
    'EOG waveform visualization (16 channels)',
    'ControlSignal-based trial segmentation',
    'Direction label generation (4/8/36 classes)',
    'Signal preprocessing (baseline, detrend, filter, normalize)',
    'Saccade onset detection (derivative thresholding)',
    'Early observation windows (20ms–200ms)',
    'Feature extraction (13 × 16 + cross-channel)',
    'Logistic Regression baseline classifier',
    'Latency-vs-accuracy experiment (all 14 subjects)',
    'Interactive research dashboard',
    'Data quality validation report',
  ];

  const planned = [
    'Multi-threshold and adaptive saccade onset detection',
    'LSTM / GRU sequential recurrent architecture',
    'Lightweight Spatial-Temporal 1D CNN baseline',
    'Confidence-based adaptive early stopping',
    'Leave-One-Subject-Out (LOSO) cross-validation',
    'Electrode subset optimization (channel reduction)',
    'Subject personalization and domain adaptation',
    'Continuous radial angle regression (sine/cosine loss)',
    'Robustness and signal-to-noise generalization studies',
    'Real-time causal streaming simulator (WebSocket)',
    'Embedded hardware deployment profiling (ESP32 / Jetson)',
    'Comprehensive statistical evaluation and publication figures',
  ];

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>
          System Overview & Milestones
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>
          Low-Latency EOG-Based Early Saccade Direction Prediction
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 32, marginTop: 16 }}>
          <div>
            <div style={{ fontSize: 36, fontWeight: 700, color: 'var(--accent)', fontFamily: "'JetBrains Mono', monospace" }}>100%</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Core Pipeline Ready</div>
          </div>
          <div>
            <div style={{ fontSize: 36, fontWeight: 700, color: 'var(--success)', fontFamily: "'JetBrains Mono', monospace" }}>13</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Modules Validated</div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16, color: 'var(--success)' }}>
            ✓ Implemented Capabilities
          </div>
          {completed.map((item, i) => (
            <div key={i} className="checklist-item">
              <span className="check-done">✓</span>
              <span>{item}</span>
            </div>
          ))}
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 16, color: 'var(--text-muted)' }}>
            ○ Technical Roadmap
          </div>
          {planned.map((item, i) => (
            <div key={i} className="checklist-item">
              <span className="check-pending">○</span>
              <span style={{ color: 'var(--text-muted)' }}>{item}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title" style={{ marginBottom: 12 }}>Research Questions & Evaluation Benchmarks</div>
        <ol style={{ color: 'var(--text-secondary)', fontSize: 13, paddingLeft: 20, lineHeight: 2 }}>
        
        </ol>
      </div>
    </div>
  );
}
