import { Link } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { Experiment, ExperimentSummary, EvaluationResult } from '../services/types';

export function ExperimentPicker({ entries, value, onChange }: { entries: ExperimentSummary[]; value: string; onChange: (id: string) => void }) {
  return <label className="control-group experiment-picker">Experiment<select value={value} onChange={e => onChange(e.target.value)}><option value="">Select experiment</option>{entries.map(e => <option key={e.experiment_id} value={e.experiment_id}>{e.config.smoke ? 'SMOKE' : 'FULL'} · {e.config.evaluation.toUpperCase()} · {e.config.subjects.length} subjects · {e.experiment_id.slice(0, 8)} · {e.status}</option>)}</select></label>;
}

export function Provenance({ experiment }: { experiment: Experiment }) {
  return <div className="evidence-strip"><span>Mode <strong>{experiment.config.smoke ? 'SMOKE' : 'FULL'} / {experiment.config.evaluation.toUpperCase()}</strong></span><span>Subjects <strong>{experiment.config.subjects.join(', ')}</strong></span><span>Processing <strong>{experiment.config.preprocessing_version}</strong></span><span>Features <strong>{experiment.config.feature_version}</strong></span><span>Dataset <strong title={experiment.dataset.fingerprint}>{experiment.dataset.fingerprint.slice(0, 12)}</strong></span><span>Recorded <strong>{new Date(experiment.timestamp).toLocaleString()}</strong></span></div>;
}

export function AccuracyChart({ results }: { results: EvaluationResult[] }) {
  const families = [...new Set(results.map(r => r.model_name))];
  const rows = [...new Set(results.map(r => r.window_ms))].sort((a, b) => a - b).map(ms => ({ window: ms, ...Object.fromEntries(results.filter(r => r.window_ms === ms).map(r => [r.model_name, r.metrics.accuracy * 100])) }));
  const colors = ['#36BCE3', '#37C991', '#E5AD38'];
  return <><div className="chart-container" style={{ height: 250 }}><ResponsiveContainer width="100%" height="100%"><LineChart data={rows} margin={{ bottom: 20, right: 15 }}><CartesianGrid stroke="var(--border)" strokeDasharray="2 4" /><XAxis dataKey="window" type="number" domain={['dataMin', 'dataMax']} stroke="var(--text-muted)" label={{ value: 'Requested observation budget (ms)', position: 'insideBottom', offset: -12, fill: 'var(--text-muted)' }} /><YAxis domain={[0, 100]} stroke="var(--text-muted)" tickFormatter={value => `${value}%`} /><Tooltip contentStyle={{ background: 'var(--panel)', border: '1px solid var(--border)' }} />{families.map((family, i) => <Line key={family} type="linear" dataKey={family} stroke={colors[i % colors.length]} name={family.replaceAll('_', ' ')} strokeWidth={2} dot={{ r: 3 }} isAnimationActive={false} />)}</LineChart></ResponsiveContainer></div><div className="chart-legend">{families.map((family, i) => <span key={family} style={{ color: colors[i % colors.length] }}>{family.replaceAll('_', ' ')}</span>)}</div></>;
}

export function ResultTable({ results, experimentId }: { results: EvaluationResult[]; experimentId: string }) {
  return <div className="table-scroll"><table className="data-table"><thead><tr><th>Model</th><th>Budget</th><th>Samples</th><th>Accuracy</th><th>Balanced</th><th>Macro F1</th><th>Predictions</th><th>Coverage</th><th>Matched accuracy</th></tr></thead><tbody>{results.map(r => <tr key={`${r.model_name}-${r.window_ms}`}><td><Link to={`/reports?experiment=${experimentId}`}>{r.model_name.replaceAll('_', ' ')}</Link></td><td>{r.window_ms} ms</td><td>{r.n_samples}</td><td>{(r.metrics.accuracy * 100).toFixed(2)}%</td><td>{(r.metrics.balanced_accuracy * 100).toFixed(2)}%</td><td>{r.metrics.macro_f1.toFixed(4)}</td><td>{r.n_predictions}</td><td>{r.source_test_trials ? `${(r.coverage * 100).toFixed(2)}%` : "Unavailable"}</td><td>{r.matched_metrics ? `${(r.matched_metrics.accuracy * 100).toFixed(2)}% (n=${r.matched_prediction_count})` : 'Unavailable'}</td></tr>)}</tbody></table></div>;
}

export function ConfusionMatrix({ result, names }: { result: EvaluationResult; names: string[] }) {
  return <div className="table-scroll"><table className="data-table confusion"><caption>Rows: target class · columns: predicted class</caption><thead><tr><th>Actual / predicted</th>{names.map(name => <th key={name}>{name}</th>)}</tr></thead><tbody>{result.metrics.confusion_matrix.map((row, i) => <tr key={names[i]}><th>{names[i]}</th>{row.map((value, j) => <td key={j} className={i === j ? 'diagonal' : ''}>{value}</td>)}</tr>)}</tbody></table></div>;
}
