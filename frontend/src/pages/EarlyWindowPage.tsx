import { useState } from 'react';
import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea, ReferenceLine } from 'recharts';

const WINDOW_DURATIONS = [20, 40, 60, 80, 100, 120, 160, 200];
const DIR_NAMES = ['Right', 'Up-Right', 'Up', 'Up-Left', 'Left', 'Down-Left', 'Down', 'Down-Right'];

export default function EarlyWindowPage() {
  const [subjectId, setSubjectId] = useState('S1');
  const [trialId, setTrialId] = useState(10);
  const [windowMs, setWindowMs] = useState(100);
  const [alignment, setAlignment] = useState<'onset' | 'cue'>('onset');

  const { data: subjects } = useFetch(() => api.subjects(), []);
  const { data, loading } = useFetch(
    () => api.earlyWindow(subjectId, trialId, windowMs, alignment),
    [subjectId, trialId, windowMs, alignment]
  );

  // Build chart from full signal with window highlighting
  const chartData = data?.full_time_ms?.map((t: number, i: number) => ({
    time: Math.round(t * 10) / 10,
    signal: data.full_signal[i],
  })) || [];

  const onsetMs = data?.onset_ms || 0;
  const windowEndMs = alignment === 'onset'
    ? onsetMs + (data?.effective_ms || 0)
    : (data?.effective_ms || 0);
  const windowStartMs = alignment === 'onset' ? onsetMs : 0;

  return (
    <div>
      {/* Controls */}
      <div className="controls-row">
        <div className="control-group">
          <span className="control-label">Subject</span>
          <select value={subjectId} onChange={e => { setSubjectId(e.target.value); setTrialId(10); }}>
            {subjects?.subjects?.map((s: any) => (
              <option key={s.subject_id} value={s.subject_id}>{s.subject_id}</option>
            ))}
          </select>
        </div>
        <div className="control-group">
          <span className="control-label">Trial</span>
          <input type="number" min={0} max={287} value={trialId}
            onChange={e => setTrialId(Number(e.target.value))} style={{ width: 80 }} />
        </div>
        <div className="control-group">
          <span className="control-label">Alignment</span>
          <div className="toggle-group">
            <button className={`toggle-btn ${alignment === 'onset' ? 'active' : ''}`}
              onClick={() => setAlignment('onset')}>Onset</button>
            <button className={`toggle-btn ${alignment === 'cue' ? 'active' : ''}`}
              onClick={() => setAlignment('cue')}>Cue</button>
          </div>
        </div>
      </div>

      {/* Window slider */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header">
          <span className="card-title">Observation Duration</span>
          <span style={{ color: 'var(--accent)', fontFamily: "'JetBrains Mono', monospace", fontSize: 20, fontWeight: 700 }}>
            {windowMs} ms
          </span>
        </div>
        <input
          type="range"
          min={20} max={200} step={1}
          value={windowMs}
          onChange={e => setWindowMs(Number(e.target.value))}
          style={{ width: '100%', accentColor: 'var(--accent)' }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: 11, marginTop: 4 }}>
          <span>20ms</span>
          {WINDOW_DURATIONS.slice(1, -1).map(d => <span key={d}>{d}ms</span>)}
          <span>200ms</span>
        </div>
      </div>

      {/* Signal with window overlay */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header">
          <span className="card-title">Outward Saccade — Channel 0</span>
          {data?.trial_metadata && (
            <span className="badge badge-info">
              True: {DIR_NAMES[data.trial_metadata.direction_label_8]} ({data.trial_metadata.target_angle_deg}°)
            </span>
          )}
        </div>
        {loading ? (
          <div className="skeleton" style={{ height: 350 }} />
        ) : (
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={11}
                  label={{ value: 'Time (ms)', position: 'bottom', offset: -5 }} />
                <YAxis stroke="var(--text-muted)" fontSize={11} />
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', fontSize: 12 }} />
                {/* Highlight the observation window */}
                <ReferenceArea x1={windowStartMs} x2={windowEndMs}
                  fill="var(--accent)" fillOpacity={0.12} stroke="var(--accent)" strokeDasharray="3 3" />
                {/* Onset marker */}
                {data?.onset_sample > 0 && alignment === 'onset' && (
                  <ReferenceLine x={onsetMs} stroke="var(--warning)" strokeDasharray="3 3"
                    label={{ value: 'Onset', fill: 'var(--warning)', fontSize: 10 }} />
                )}
                {/* Window end marker */}
                <ReferenceLine x={windowEndMs} stroke="var(--accent)" strokeWidth={2}
                  label={{ value: `${windowMs}ms`, fill: 'var(--accent)', fontSize: 10, position: 'top' }} />
                <Line type="monotone" dataKey="signal" stroke="var(--text-secondary)" dot={false} strokeWidth={1.5} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Info cards */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))' }}>
        <div className="stat-card">
          <div className="stat-value" style={{ fontSize: 20 }}>{data?.n_samples || '—'}</div>
          <div className="stat-label">Samples</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ fontSize: 20 }}>{data?.effective_ms || '—'}ms</div>
          <div className="stat-label">Effective Duration</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ fontSize: 20 }}>{data?.onset_ms || '—'}ms</div>
          <div className="stat-label">Onset Latency</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ fontSize: 20 }}>{data?.n_features || '—'}</div>
          <div className="stat-label">Features</div>
        </div>
      </div>

      {/* Concept explanation */}
      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title" style={{ marginBottom: 8 }}>How This Works</div>
        <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.7 }}>
          The <span style={{ color: 'var(--accent)' }}>highlighted region</span> shows the only data
          available to the classifier at {windowMs}ms. Everything after the
          <span style={{ color: 'var(--accent)' }}> vertical line</span> is the future — the model
          cannot see it. As the slider increases, more of the saccade waveform becomes visible,
          and prediction accuracy improves. The research question is: how early can we predict
          direction reliably?
        </p>
      </div>
    </div>
  );
}
