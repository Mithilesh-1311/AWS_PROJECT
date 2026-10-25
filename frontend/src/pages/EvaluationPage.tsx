import { useState } from 'react';
import { useExperiment } from '../hooks/useExperiment';
import { ExperimentPicker, Provenance, AccuracyChart, ResultTable, ConfusionMatrix } from '../components/ExperimentPanels';
import { Loading, Notice } from '../components/ResearchPanels';
import LegacyExperiments from './ExperimentsPage';

export default function EvaluationPage() {
  const [legacy, setLegacy] = useState(false);
  const { list, detail, experimentId, setExperimentId } = useExperiment();
  const [selected, setSelected] = useState('');
  const results = detail.data?.results || [];
  const current = results.find(r => `${r.model_name}:${r.window_ms}` === selected) || results[0];
  return <><div className="page-heading"><div><h1>Model evaluation</h1><p>Compare observation budgets with subject-independent evidence.</p></div><button onClick={() => setLegacy(v => !v)}>{legacy ? 'Show corrected experiments' : 'Show legacy retrospective reports'}</button></div>
    {legacy ? <LegacyExperiments /> : <><ExperimentPicker entries={list.data?.experiments || []} value={experimentId} onChange={id => { setExperimentId(id); setSelected(''); }} />
      {(list.error || detail.error) && <Notice message={list.error || detail.error!} />}
      {detail.data && <Provenance experiment={detail.data} />}
      {list.loading || detail.loading ? <Loading /> : results.length ? <><div className="card"><h2>Accuracy vs observation budget</h2><AccuracyChart results={results} /><p className="muted">All-eligible metrics can have different trial counts. Matched metrics use common eligible 400 ms reference IDs. Observation budget is not cue-to-decision latency.</p></div><div className="card section"><h2>Comparison table</h2><ResultTable results={results} experimentId={experimentId} /></div>
        <label className="control-group">Detailed result<select value={current ? `${current.model_name}:${current.window_ms}` : ''} onChange={e => setSelected(e.target.value)}>{results.map(r => <option key={`${r.model_name}:${r.window_ms}`} value={`${r.model_name}:${r.window_ms}`}>{r.model_name} · {r.window_ms} ms</option>)}</select></label>
        {current && <><div className="card section"><h2>Confusion matrix</h2><ConfusionMatrix result={current} names={detail.data!.class_names} /></div><div className="card section"><h2>Held-out subjects</h2>{current.subject_accuracy_interval && <p className="muted">Subject bootstrap interval: {(current.subject_accuracy_interval.low * 100).toFixed(2)}–{(current.subject_accuracy_interval.high * 100).toFixed(2)}%. {current.subject_accuracy_interval.method}</p>}<div className="table-scroll"><table className="data-table"><thead><tr><th>Test subjects</th><th>Train trials</th><th>Test trials</th><th>Accuracy</th><th>Macro F1</th></tr></thead><tbody>{current.folds.map((fold, i) => <tr key={i}><td>{fold.test_subjects.join(', ')}</td><td>{fold.n_train}</td><td>{fold.n_test}</td><td>{(fold.metrics.accuracy * 100).toFixed(2)}%</td><td>{fold.metrics.macro_f1.toFixed(4)}</td></tr>)}</tbody></table></div></div></>}</> : <div className="notice">No completed results for this experiment. Check its job state on Overview.</div>}
    </>}
  </>;
}
