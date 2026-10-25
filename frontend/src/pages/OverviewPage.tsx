import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';

const PIPELINE_STEPS = [
  'EOG Signal', '→', 'Saccade Onset', '→', 'Partial Window', '→',
  'Feature Extraction', '→', 'Direction Prediction', '→', 'Latency / Accuracy'
];

export default function OverviewPage() {
  const { data: summary, loading } = useFetch(() => api.datasetSummary(), []);

  if (loading) return <div className="skeleton" style={{ height: 400 }} />;

  return (
    <div>
      {/* Hero */}
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
          Low-Latency EOG-Based Early Intent Detection
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 14, maxWidth: 600, margin: '0 auto' }}>
          Predicting saccadic eye-movement direction from partial electrooculographic observations.
        </p>
      </div>

      {/* Stats grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{summary?.n_subjects || '—'}</div>
          <div className="stat-label">Subjects</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{summary?.n_channels || '—'}</div>
          <div className="stat-label">EOG Channels</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{summary?.sampling_rate_hz || '—'}</div>
          <div className="stat-label">Sampling Rate (Hz)</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{summary?.total_trials?.toLocaleString() || '—'}</div>
          <div className="stat-label">Total Trials</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{summary?.n_directions || '—'}</div>
          <div className="stat-label">Target Directions</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{summary?.target_magnitude_deg || '—'}°</div>
          <div className="stat-label">Target Magnitude</div>
        </div>
      </div>

      {/* Pipeline */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">Research Pipeline</span>
        </div>
        <div className="pipeline">
          {PIPELINE_STEPS.map((step, i) =>
            step === '→'
              ? <span key={i} className="pipeline-arrow">→</span>
              : <div key={i} className="pipeline-step">{step}</div>
          )}
        </div>
      </div>

      {/* Window specs */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">Observation Windows</span>
          <span className="card-subtitle">Rounding: ceil(T_ms × 256 / 1000)</span>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Requested (ms)</th>
              <th>Samples</th>
              <th>Effective (ms)</th>
            </tr>
          </thead>
          <tbody>
            {summary?.window_specs?.map((w: any) => (
              <tr key={w.requested_ms}>
                <td>{w.requested_ms}</td>
                <td>{w.n_samples}</td>
                <td>{w.effective_ms}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pipeline Capabilities */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">System Pipeline Status</span>
          <span className="badge badge-success">Active</span>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.6 }}>
          End-to-end 16-channel EOG acquisition, causal baseline centering, physiological saccade onset detection, early-window extraction (20ms–200ms), and multi-class directional decoding pipeline operational.
        </p>
      </div>
    </div>
  );
}
