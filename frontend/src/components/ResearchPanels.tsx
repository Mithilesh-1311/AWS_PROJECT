import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Brush } from 'recharts';
import { api } from '../services/api';
import { useFetch } from '../hooks/useFetch';
import type { Prediction, WindowMetadata } from '../services/types';

import { Notice } from './RequestState';
export { Notice, Loading } from './RequestState';

export function TrialControls({ subjectId, trialId, setSubjectId, setTrialId }: { subjectId: string; trialId: number; setSubjectId: (s: string) => void; setTrialId: (n: number) => void }) {
  const { data, error } = useFetch(api.datasetSummary);
  return <><div className="controls-row"><label className="control-group">Subject<select value={subjectId} onChange={e => setSubjectId(e.target.value)}>
    {(data?.subject_ids || [subjectId]).map(s => <option key={s}>{s}</option>)}</select></label>
    <label className="control-group">Trial index<input type="number" min={0} max={287} value={trialId} onChange={e => setTrialId(Number(e.target.value))} /></label>
    <span className="muted">Zero-based trial index · recorded outward phase</span></div>{error && <Notice message={error} />}</>;
}

export function Pipeline() {
  const labels = [['Recorded EOG', '16 channels'], ['Calibration + filter', '25 cue samples'], ['Onset + window', 'crossing / confirmation'], ['212 features', 'physical-v2'], ['Saved model', '8 directions'], ['Prediction', 'class + timing']];
  return <div className="card"><h2>System pipeline</h2><p className="muted">Functional pipeline · cue-triggered recorded-data research</p>
    <div className="pipeline-svg"><svg viewBox="0 0 440 440" role="img" aria-label="Recorded EOG passes through calibration, onset and windows, features and model to a direction prediction. Target labels are separate evaluation metadata.">
      {labels.map(([name, detail], i) => <g key={name} transform={`translate(22,${12 + i * 62})`}>
        <rect width="396" height="46" fill="var(--selected)" stroke="var(--border)" />
        <text x="12" y="19" fill="var(--text-primary)" fontSize="13">{name}</text>
        <text x="12" y="35" fill="var(--text-muted)" fontSize="10">{detail}</text>
        {i < 5 && <path d="M198 46v16m-4-5 4 5 4-5" stroke="var(--accent)" fill="none" />}
      </g>)}
      <path d="M30 399h380" stroke="var(--warning)" strokeDasharray="4 3" /><text x="30" y="420" fill="var(--warning)" fontSize="11">Target / control labels → evaluation metadata only</text>
    </svg></div></div>;
}

export function Waveform({ rows, channels, window: observation }: { rows: Record<string, number>[]; channels: string[]; window?: WindowMetadata }) {
  const [chartVersion, resetChart] = useState(0);
  const colors = ['#36BCE3', '#37C991', '#E5AD38', '#F16D70'];
  return <><button className="chart-reset" onClick={() => resetChart(value => value + 1)} disabled={rows.length <= 32}>Reset zoom</button><div className="chart-container signal-chart"><ResponsiveContainer width="100%" height="100%"><LineChart key={chartVersion} data={rows} margin={{ right: 15, bottom: 20 }}>
    <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" /><XAxis dataKey="time" type="number" domain={['dataMin', 'dataMax']} stroke="var(--text-muted)" tick={{ fontSize: 11 }} tickFormatter={value => Number(value).toFixed(0)} label={{ value: 'Time from cue (ms)', position: 'insideBottom', offset: -12, fill: 'var(--text-muted)' }} />
    <YAxis width={55} stroke="var(--text-muted)" tick={{ fontSize: 10 }} /><Tooltip contentStyle={{ background: 'var(--panel)', border: '1px solid var(--border)', color: 'var(--text-primary)' }} />
    {channels.map((channel, index) => <Line key={channel} dataKey={channel} name={`Ch ${channel}`} stroke={colors[index % colors.length]} strokeWidth={1.4} dot={false} isAnimationActive={false} type="linear" />)}
    {observation?.crossing_sample != null && <ReferenceLine x={observation.crossing_sample / 256 * 1000} stroke="var(--warning)" label={{ value: 'Crossing', fill: 'var(--warning)', position: 'insideTopLeft' }} />}
    {observation?.confirmation_sample != null && <ReferenceLine x={observation.confirmation_sample / 256 * 1000} stroke="var(--text-muted)" strokeDasharray="4 2" />}
    {observation && <ReferenceLine x={observation.cue_to_decision_ms} stroke="var(--success)" label={{ value: 'Decision ready', fill: 'var(--success)', position: 'insideBottomRight' }} />}
    {rows.length > 32 && <Brush dataKey="time" height={18} stroke="var(--border)" fill="var(--panel)" travellerWidth={8} />}
  </LineChart></ResponsiveContainer></div><p className="muted">Amplitude: recorded units; voltage scale unverified. Raw samples shown; model uses the complete selected channel set.</p>
    <details><summary>Accessible sample table ({rows.length} samples)</summary><div className="table-scroll"><table className="data-table"><thead><tr><th>Time (ms)</th>{channels.map(c => <th key={c}>Ch {c}</th>)}</tr></thead><tbody>{rows.map((row, i) => <tr key={i}><td>{row.time.toFixed(2)}</td>{channels.map(c => <td key={c}>{row[c]?.toFixed(4)}</td>)}</tr>)}</tbody></table></div></details></>;
}

export function PredictionView({ prediction }: { prediction: Prediction }) {
  if (prediction.state === 'abstained') return <div className="notice">Prediction withheld: {prediction.reason}. Select another trial.</div>;
  return <div className="card prediction-result"><div className="card-header"><h2>Predicted direction</h2><span className="badge badge-success">MODEL OUTPUT</span></div>
    <div className="prediction-heading">{prediction.predicted_direction}</div>
    <p className="muted">{prediction.score_semantics.replaceAll('_', ' ')} · these are not calibrated confidence estimates</p>
    <div className="score-list">{prediction.class_names.map((name, index) => <div key={name} className="score-row"><span>{name}</span><meter min={0} max={1} value={prediction.scores[index]} aria-label={`${name} score`} /><span>{(prediction.scores[index] * 100).toFixed(1)}%</span></div>)}</div>
    <dl className="timing-list"><div><dt>Requested window</dt><dd>{prediction.window.requested_ms} ms</dd></div><div><dt>Samples / budget / span</dt><dd>{prediction.window.n_samples} / {prediction.window.sample_budget_ms.toFixed(2)} / {prediction.window.sample_span_ms.toFixed(2)} ms</dd></div><div><dt>Calibration budget</dt><dd>{(prediction.window.calibration_samples / 256 * 1000).toFixed(2)} ms</dd></div><div><dt>Cue → decision readiness</dt><dd>{prediction.window.cue_to_decision_ms.toFixed(2)} ms</dd></div><div><dt>Confirmation delay</dt><dd>{prediction.window.confirmation_delay_ms?.toFixed(2) ?? 'Unavailable'} ms</dd></div><div><dt>Feature / model compute</dt><dd>{prediction.feature_ms.toFixed(2)} / {prediction.inference_ms.toFixed(2)} ms</dd></div></dl>
    {prediction.evaluation && <p>Evaluation target: <strong>{prediction.class_names[prediction.evaluation.target_class]}</strong> · {prediction.evaluation.target_angle_deg}°</p>}
    {prediction.warnings.map(warning => <p className="muted" key={warning}>{warning}</p>)}
    <p className="provenance">Model {prediction.model_id}<br /><Link to={`/reports?experiment=${prediction.experiment_id}`}>Inspect experiment provenance</Link></p>
  </div>;
}

export function JobsPanel() {
  const [tick, setTick] = useState(0);
  const [actionError, setActionError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { data, error } = useFetch(api.jobs, [tick]);
  useEffect(() => { const interval = setInterval(() => setTick(t => t + 1), 5000); return () => clearInterval(interval); }, []);
  async function create() { setSubmitting(true); setActionError(null); try { await api.createJob(); setTick(t => t + 1); } catch (e) { setActionError(e instanceof Error ? e.message : 'Job failed'); } finally { setSubmitting(false); } }
  async function cancel(id: string) { try { await api.cancelJob(id); setTick(t => t + 1); } catch (e) { setActionError(e instanceof Error ? e.message : 'Cancellation failed'); } }
  return <div className="card"><div className="card-header"><div><h2>Experiment worker</h2><p className="muted">{data ? data.worker_ready ? 'Worker heartbeat received' : 'Worker offline — run python -m scripts.worker' : 'Checking worker'}</p></div><button onClick={create} disabled={submitting || !data?.worker_ready}>{submitting ? 'Submitting…' : 'Run S1–S3 smoke job'}</button></div>
    {(error || actionError) && <Notice message={error || actionError!} />}
    {!data?.jobs.length && <p className="muted">No jobs recorded. Smoke jobs use real trials and remain distinct from full evaluation.</p>}
    <div className="job-list">{data?.jobs.slice(0, 5).map(job => <div key={job.id} className="job-row"><div><strong>{job.state.toUpperCase()}</strong><span className="mono">{job.id.slice(0, 8)}</span><p className="muted">{job.progress.stage || 'Awaiting worker'}{job.progress.total ? ` · ${job.progress.completed} / ${job.progress.total}` : ''}</p>{job.error && <p role="alert">{job.error.message}</p>}</div>{['queued', 'running'].includes(job.state) ? <button onClick={() => cancel(job.id)}>Cancel</button> : job.result && <Link to={`/reports?experiment=${job.result.experiment_id}`}>Result</Link>}</div>)}</div>
  </div>;
}
