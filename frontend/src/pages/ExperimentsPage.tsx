import { useState } from 'react';
import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';
import { Notice } from '../components/RequestState';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';



export default function ExperimentsPage() {
  const { data: results, loading, error, refetch } = useFetch(api.latestResults, []);
  const [selectedWindow, setSelectedWindow] = useState<number | null>(null);

  // Latency-accuracy chart data
  const chartData = results?.window_results?.map((w) => ({
    window: w.effective_ms,
    label: `${w.window_ms}ms`,
    accuracy: +(w.accuracy * 100).toFixed(1),
    macro_f1: +(w.macro_f1 * 100).toFixed(1),
    samples: w.n_samples,
  })) || [];

  // Selected window confusion matrix
  const selIdx = selectedWindow ?? Math.min(4, (results?.window_results?.length || 1) - 1);
  const selResult = results?.window_results?.[selIdx];
  const DIR_NAMES = results?.class_names ?? [];
  const cm = selResult?.confusion_matrix || [];

  if (error) return <Notice message={error} retry={refetch} />;
  return (
    <div>
      <div style={{ marginBottom: 8 }}>
        <span className="badge badge-info" style={{ fontSize: 12 }}>
          Baseline Direction Classification Benchmark
        </span>
      </div>

      {loading ? (
        <div className="skeleton" style={{ height: 400 }} />
      ) : (
        <>
          {/* Experiment info */}
          <div className="controls-row" style={{ marginBottom: 16 }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Model: <strong style={{ color: 'var(--text-primary)' }}>{results?.model_name}</strong>
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Classes: <strong style={{ color: 'var(--text-primary)' }}>{results?.n_classes}</strong>
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Alignment: <strong style={{ color: 'var(--text-primary)' }}>{results?.alignment}</strong>
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Split: <strong style={{ color: 'var(--text-primary)' }}>{results?.split_method}</strong>
            </span>
          </div>

          {/* Latency vs Accuracy chart */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header">
              <span className="card-title">Classification Performance vs. Observation Latency</span>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="window" type="number" domain={['dataMin', 'dataMax']} stroke="var(--text-muted)" fontSize={11}
                    label={{ value: 'Effective Observation Duration (ms)', position: 'bottom', offset: -5 }} />
                  <YAxis domain={[0, 100]} stroke="var(--text-muted)" fontSize={11}
                    label={{ value: '%', angle: -90, position: 'insideLeft' }} />
                  <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', fontSize: 12 }} />
                  <Legend />
                  <Line type="linear" isAnimationActive={false} dataKey="accuracy" stroke="var(--accent)" strokeWidth={2.5}
                    dot={{ fill: 'var(--accent)', r: 4 }} name="Accuracy (%)" />
                  <Line type="linear" isAnimationActive={false} dataKey="macro_f1" stroke="#10b981" strokeWidth={2.5}
                    dot={{ fill: '#10b981', r: 4 }} name="Macro F1 (%)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Results table */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header">
              <span className="card-title">Per-Window Results</span>
            </div>
            <div className="table-scroll"><table className="data-table">
              <thead>
                <tr>
                  <th>Window</th><th>Samples</th><th>Eff. ms</th>
                  <th>Accuracy</th><th>Macro F1</th><th>Train</th><th>Test</th><th></th>
                </tr>
              </thead>
              <tbody>
                {results?.window_results?.map((w, i: number) => (
                  <tr key={i} style={i === selIdx ? { background: 'var(--accent-glow)' } : {}}>
                    <td>{w.window_ms}ms</td>
                    <td>{w.n_samples}</td>
                    <td>{w.effective_ms}ms</td>
                    <td style={{ color: 'var(--accent)' }}>{(w.accuracy * 100).toFixed(1)}%</td>
                    <td style={{ color: '#10b981' }}>{(w.macro_f1 * 100).toFixed(1)}%</td>
                    <td>{w.n_train}</td>
                    <td>{w.n_test}</td>
                    <td>
                      <button className="toggle-btn active" style={{ padding: '2px 8px', fontSize: 11 }}
                        onClick={() => setSelectedWindow(i)}>View</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          </div>

          {/* Confusion Matrix */}
          {selResult && (
            <div className="grid-2">
              <div className="card">
                <div className="card-header">
                  <span className="card-title">Confusion Matrix — {selResult.window_ms}ms</span>
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <div className="table-scroll"><table className="data-table" style={{ fontSize: 11 }}>
                    <thead>
                      <tr>
                        <th>Pred →</th>
                        {DIR_NAMES.slice(0, results?.n_classes || 8).map((n, i) => (
                          <th key={i} style={{ textTransform: 'none', fontSize: 10 }}>{n.slice(0, 2)}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {cm.map((row: number[], ri: number) => (
                        <tr key={ri}>
                          <td style={{ fontWeight: 600, fontSize: 10 }}>{DIR_NAMES[ri]?.slice(0, 4)}</td>
                          {row.map((val: number, ci: number) => {
                            const isMax = val === Math.max(...row);
                            const isDiag = ri === ci;
                            return (
                              <td key={ci} style={{
                                background: isDiag ? 'rgba(6,182,212,0.15)' : (isMax && !isDiag ? 'rgba(239,68,68,0.1)' : ''),
                                color: isDiag ? 'var(--accent)' : 'var(--text-secondary)',
                                textAlign: 'center',
                                fontWeight: isDiag ? 700 : 400,
                              }}>{val}</td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table></div>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <span className="card-title">Per-Class Metrics — {selResult.window_ms}ms</span>
                </div>
                <div className="table-scroll"><table className="data-table">
                  <thead>
                    <tr><th>Direction</th><th>Precision</th><th>Recall</th><th>F1</th></tr>
                  </thead>
                  <tbody>
                    {DIR_NAMES.slice(0, results?.n_classes || 8).map((name, i) => (
                      <tr key={i}>
                        <td>{name}</td>
                        <td>{(selResult.per_class_precision[i] * 100).toFixed(1)}%</td>
                        <td>{(selResult.per_class_recall[i] * 100).toFixed(1)}%</td>
                        <td>{(selResult.per_class_f1[i] * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table></div>
              </div>
            </div>
          )}

          {/* Subject split info */}
          <div className="card" style={{ marginTop: 16 }}>
            <div className="card-title" style={{ marginBottom: 8 }}>Evaluation Details</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              <p><strong>Train subjects:</strong> {results?.subjects_train?.join(', ')}</p>
              <p><strong>Test subjects:</strong> {results?.subjects_test?.join(', ')}</p>
              <p style={{ color: 'var(--text-muted)', marginTop: 8 }}>
                ℹ Historical subject holdout. This retrospective pipeline is distinct from the corrected causal LOSO experiments.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
