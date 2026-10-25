import { useState } from 'react';
import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

export default function SignalPage() {
  const [subjectId, setSubjectId] = useState('S1');
  const [trialId, setTrialId] = useState(5);
  const [baseline, setBaseline] = useState(true);
  const [detrend, setDetrend] = useState(false);
  const [highpass, setHighpass] = useState(false);
  const [normalize, setNormalize] = useState(false);

  const { data: subjects } = useFetch(() => api.subjects(), []);
  const { data, loading } = useFetch(
    () => api.signalProcessing(subjectId, trialId, {
      baseline_correct: String(baseline),
      detrend: String(detrend),
      highpass: String(highpass),
      normalize: String(normalize),
    }),
    [subjectId, trialId, baseline, detrend, highpass, normalize]
  );

  // Prepare chart data for raw vs processed (channel 0)
  const rawData = data?.time_ms?.map((t: number, i: number) => ({
    time: Math.round(t * 10) / 10,
    raw: data.raw_data?.['0']?.[i],
    processed: data.processed_data?.['0']?.[i],
  })) || [];

  const derivData = data?.onset?.derivative_signal?.map((v: number, i: number) => ({
    idx: i,
    value: v,
  })) || [];

  const onsetMs = data?.onset?.onset_ms;

  return (
    <div>
      <div className="controls-row">
        <div className="control-group">
          <span className="control-label">Subject</span>
          <select value={subjectId} onChange={e => { setSubjectId(e.target.value); setTrialId(5); }}>
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
        <label style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: 'var(--text-secondary)' }}>
          <input type="checkbox" checked={baseline} onChange={e => setBaseline(e.target.checked)} /> Baseline
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: 'var(--text-secondary)' }}>
          <input type="checkbox" checked={detrend} onChange={e => setDetrend(e.target.checked)} /> Detrend
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: 'var(--text-secondary)' }}>
          <input type="checkbox" checked={highpass} onChange={e => setHighpass(e.target.checked)} /> High-pass
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: 'var(--text-secondary)' }}>
          <input type="checkbox" checked={normalize} onChange={e => setNormalize(e.target.checked)} /> Normalize
        </label>
      </div>

      {loading ? (
        <div className="skeleton" style={{ height: 300, marginBottom: 16 }} />
      ) : (
        <>
          {/* Raw vs Processed */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header">
              <span className="card-title">Raw vs Processed — Channel 0</span>
              {data?.onset?.reliable
                ? <span className="badge badge-success">Onset: {onsetMs?.toFixed(1)}ms</span>
                : <span className="badge badge-warning">Onset: {data?.onset?.reason}</span>
              }
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={rawData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={11} />
                  <YAxis stroke="var(--text-muted)" fontSize={11} />
                  <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', fontSize: 12 }} />
                  <Line type="monotone" dataKey="raw" stroke="var(--text-muted)" dot={false} strokeWidth={1} name="Raw" strokeDasharray="4 2" />
                  <Line type="monotone" dataKey="processed" stroke="var(--accent)" dot={false} strokeWidth={1.5} name="Processed" />
                  {onsetMs != null && <ReferenceLine x={onsetMs} stroke="var(--warning)" strokeDasharray="3 3" label={{ value: 'Onset', fill: 'var(--warning)', fontSize: 10 }} />}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Derivative */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header">
              <span className="card-title">Derivative (Onset Detection Signal)</span>
              <span className="card-subtitle">Threshold: {data?.onset?.threshold?.toFixed(4)}</span>
            </div>
            <div className="chart-container" style={{ height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={derivData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="idx" stroke="var(--text-muted)" fontSize={11} />
                  <YAxis stroke="var(--text-muted)" fontSize={11} />
                  <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', fontSize: 12 }} />
                  <Line type="monotone" dataKey="value" stroke="#10b981" dot={false} strokeWidth={1} />
                  {data?.onset?.threshold && (
                    <ReferenceLine y={data.onset.threshold} stroke="var(--danger)" strokeDasharray="3 3" />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Info */}
          <div className="card">
            <div className="card-title" style={{ marginBottom: 8 }}>Preprocessing Notes</div>
            <ul style={{ color: 'var(--text-secondary)', fontSize: 12, paddingLeft: 20 }}>
              <li>Acquisition already applied: 30 Hz low-pass, 50 Hz notch filter</li>
              <li>Baseline correction: subtracts mean of initial ~100ms quiet period</li>
              <li>High-pass filter: 1st-order Butterworth at 0.1 Hz (zero-phase = non-causal, for offline use)</li>
              <li>Onset detection: derivative thresholding with MAD-based noise estimation</li>
              <li style={{ color: 'var(--warning)' }}>⚠ Zero-phase filtering is non-causal and cannot be claimed as real-time compatible</li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
