import { useState } from 'react';
import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function DatasetPage() {
  const [subjectId, setSubjectId] = useState('S1');
  const [trialId, setTrialId] = useState(0);
  const [selectedChannels, setSelectedChannels] = useState('0,1,2,3');

  const { data: subjects } = useFetch(() => api.subjects(), []);
  const { data: trials } = useFetch(() => api.trials(subjectId), [subjectId]);
  const { data: signal, loading: sigLoading } = useFetch(
    () => api.trialSignal(subjectId, trialId, {
      channels: selectedChannels,
      phase: 'outward',
      preprocess: 'true',
    }),
    [subjectId, trialId, selectedChannels]
  );

  const COLORS = ['#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
  const currentTrial = trials?.trials?.[trialId];

  // Prepare chart data
  const chartData = signal?.time_ms?.map((t: number, i: number) => {
    const point: any = { time: Math.round(t * 10) / 10 };
    Object.keys(signal.data || {}).forEach((ch: string) => {
      point[`ch${ch}`] = signal.data[ch][i];
    });
    return point;
  }) || [];

  return (
    <div>
      {/* Controls */}
      <div className="controls-row">
        <div className="control-group">
          <span className="control-label">Subject</span>
          <select value={subjectId} onChange={e => { setSubjectId(e.target.value); setTrialId(0); }}>
            {subjects?.subjects?.map((s: any) => (
              <option key={s.subject_id} value={s.subject_id}>{s.subject_id} ({s.n_trials} trials)</option>
            ))}
          </select>
        </div>
        <div className="control-group">
          <span className="control-label">Trial</span>
          <select value={trialId} onChange={e => setTrialId(Number(e.target.value))}>
            {trials?.trials?.slice(0, 50).map((t: any) => (
              <option key={t.trial_id} value={t.trial_id}>
                #{t.trial_id} — {t.direction_label_8_name} ({t.target_angle_deg}°)
              </option>
            ))}
          </select>
        </div>
        <div className="control-group">
          <span className="control-label">Channels (comma-sep)</span>
          <input
            type="text"
            value={selectedChannels}
            onChange={e => setSelectedChannels(e.target.value)}
            style={{ width: 120 }}
          />
        </div>
      </div>

      {/* Signal chart */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header">
          <span className="card-title">EOG Waveform — Outward Saccade</span>
          {currentTrial && (
            <span className="badge badge-info">
              Target: {currentTrial.direction_label_8_name} ({currentTrial.target_angle_deg}°)
            </span>
          )}
        </div>
        {sigLoading ? (
          <div className="skeleton" style={{ height: 300 }} />
        ) : (
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="time" label={{ value: 'Time (ms)', position: 'bottom' }}
                  stroke="var(--text-muted)" fontSize={11} />
                <YAxis stroke="var(--text-muted)" fontSize={11}
                  label={{ value: 'µV', angle: -90, position: 'insideLeft' }} />
                <Tooltip
                  contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', fontSize: 12 }}
                  labelStyle={{ color: 'var(--text-muted)' }}
                />
                {Object.keys(signal?.data || {}).map((ch, i) => (
                  <Line key={ch} type="monotone" dataKey={`ch${ch}`} stroke={COLORS[i % COLORS.length]}
                    dot={false} strokeWidth={1.5} name={`Ch ${ch}`} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Trial metadata */}
      {currentTrial && (
        <div className="grid-2">
          <div className="card">
            <div className="card-title" style={{ marginBottom: 12 }}>Trial Metadata</div>
            <table className="data-table">
              <tbody>
                <tr><td>Target H°</td><td>{currentTrial.target_horizontal_deg}</td></tr>
                <tr><td>Target V°</td><td>{currentTrial.target_vertical_deg}</td></tr>
                <tr><td>Direction</td><td>{currentTrial.target_angle_deg}°</td></tr>
                <tr><td>8-Class</td><td>{currentTrial.direction_label_8_name}</td></tr>
                <tr><td>Outward samples</td><td>{currentTrial.outward_end - currentTrial.outward_start}</td></tr>
              </tbody>
            </table>
          </div>
          <div className="card">
            <div className="card-title" style={{ marginBottom: 12 }}>Direction Compass</div>
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
              <svg width="180" height="180" viewBox="-100 -100 200 200">
                <circle cx="0" cy="0" r="85" fill="none" stroke="var(--border)" strokeWidth="1" />
                <circle cx="0" cy="0" r="45" fill="none" stroke="var(--border)" strokeWidth="0.5" />
                {/* Direction labels */}
                {['R', 'UR', 'U', 'UL', 'L', 'DL', 'D', 'DR'].map((label, i) => {
                  const angle = (i * 45) * Math.PI / 180;
                  const x = Math.cos(angle) * 95;
                  const y = -Math.sin(angle) * 95;
                  return <text key={label} x={x} y={y} textAnchor="middle" dominantBaseline="middle"
                    fill="var(--text-muted)" fontSize="10">{label}</text>;
                })}
                {/* Target arrow */}
                {(() => {
                  const rad = currentTrial.target_angle_deg * Math.PI / 180;
                  const x = Math.cos(rad) * 70;
                  const y = -Math.sin(rad) * 70;
                  return <line x1="0" y1="0" x2={x} y2={y} stroke="var(--accent)" strokeWidth="3"
                    markerEnd="url(#arrowhead)" />;
                })()}
                <defs>
                  <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="var(--accent)" />
                  </marker>
                </defs>
                <circle cx="0" cy="0" r="3" fill="var(--accent)" />
              </svg>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
