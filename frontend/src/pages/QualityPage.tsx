import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';

const DIR_NAMES = ['Right', 'Up-Right', 'Up', 'Up-Left', 'Left', 'Down-Left', 'Down', 'Down-Right'];

export default function QualityPage() {
  const { data, loading } = useFetch(() => api.dataQuality(), []);

  if (loading) return <div className="skeleton" style={{ height: 600 }} />;

  return (
    <div>
      {/* Overall status */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header">
          <span className="card-title">Dataset Validation</span>
          {data?.all_passed
            ? <span className="badge badge-success">ALL PASSED</span>
            : <span className="badge badge-danger">ISSUES FOUND</span>
          }
        </div>
        <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
          <div className="stat-card">
            <div className="stat-value">{data?.n_subjects}</div>
            <div className="stat-label">Subjects Validated</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ color: data?.total_anomalies > 0 ? 'var(--warning)' : 'var(--success)' }}>
              {data?.total_anomalies}
            </div>
            <div className="stat-label">Total Anomalies</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{data?.subjects?.filter((s: any) => s.passed).length}</div>
            <div className="stat-label">Subjects Passed</div>
          </div>
        </div>
      </div>

      {/* Per-subject table */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-title" style={{ marginBottom: 12 }}>Per-Subject Validation</div>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Subject</th><th>Status</th><th>Channels</th><th>Samples</th>
                <th>Trials</th><th>PD (m)</th><th>Dist (m)</th><th>NaN</th><th>CS Values</th><th>Anomalies</th>
              </tr>
            </thead>
            <tbody>
              {data?.subjects?.map((s: any) => (
                <tr key={s.subject_id}>
                  <td style={{ fontWeight: 600 }}>{s.subject_id}</td>
                  <td>
                    <span className={`badge ${s.passed ? 'badge-success' : 'badge-danger'}`}>
                      {s.passed ? 'PASS' : 'FAIL'}
                    </span>
                  </td>
                  <td>{s.n_channels}</td>
                  <td>{s.n_samples?.toLocaleString()}</td>
                  <td>{s.n_trials}</td>
                  <td>{s.pd}</td>
                  <td>{s.dist_screen}</td>
                  <td>{s.nan_count}</td>
                  <td>{s.control_signal_values?.join(', ')}</td>
                  <td style={{ maxWidth: 200, fontSize: 11, color: 'var(--warning)' }}>
                    {s.anomalies?.map((a: string, i: number) => (
                      <div key={i}>{a}</div>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Direction distribution */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-title" style={{ marginBottom: 12 }}>Direction Distribution (8-class, per subject)</div>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Subject</th>
                {DIR_NAMES.map(d => <th key={d}>{d.slice(0, 3)}</th>)}
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {data?.subjects?.map((s: any) => {
                const dist = s.direction_distribution || {};
                const total = Object.values(dist).reduce((a: any, b: any) => a + b, 0) as number;
                return (
                  <tr key={s.subject_id}>
                    <td style={{ fontWeight: 600 }}>{s.subject_id}</td>
                    {Array.from({ length: 8 }, (_, i) => (
                      <td key={i}>{dist[String(i)] || 0}</td>
                    ))}
                    <td style={{ fontWeight: 600, color: 'var(--accent)' }}>{total}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* CS=30 anomaly explanation */}
      <div className="card" style={{ borderColor: 'rgba(245, 158, 11, 0.3)' }}>
        <div className="card-title" style={{ marginBottom: 8, color: 'var(--warning)' }}>
          ControlSignal Value 30 — Anomaly Report
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
          All 14 subjects contain exactly <strong>one sample</strong> with ControlSignal = 30,
          located at the <strong>very last sample</strong> of each recording.
          This is a <strong>recording termination marker</strong>, not an experimental condition.
        </p>
        <p style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 8 }}>
          <strong>Handling:</strong> Excluded from trial segmentation. Does not affect any trial boundaries or labels.
        </p>
      </div>
    </div>
  );
}
