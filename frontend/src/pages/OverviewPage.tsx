import { Link } from 'react-router-dom';
import { useFetch } from '../hooks/useFetch';
import { useExperiment } from '../hooks/useExperiment';
import { api } from '../services/api';
import { ExperimentPicker, Provenance, AccuracyChart, ResultTable } from '../components/ExperimentPanels';
import { JobsPanel, Pipeline, Notice, Waveform, Loading } from '../components/ResearchPanels';

export default function OverviewPage() {
  const summary = useFetch(api.datasetSummary);
  const signal = useFetch(abort => api.trialSignal('S1', 0, { channels: '0,1,2', phase: 'outward' }, abort));
  const { list, detail, experimentId, setExperimentId } = useExperiment();
  const results = detail.data?.results || [];
  const primary = results.find(r => r.model_name === 'logistic_regression' && r.window_ms === 100) || results[0];
  const metrics = [
    { label: 'Recorded subjects', value: summary.data?.n_subjects, to: '/dataset' },
    { label: 'Validated trials', value: summary.data?.total_trials.toLocaleString(), to: '/quality' },
    { label: 'Channels / Hz', value: summary.data ? `${summary.data.n_channels} / ${summary.data.sampling_rate_hz}` : undefined, to: '/signal' },
    { label: primary ? `${primary.window_ms} ms · accuracy` : 'Selected accuracy', value: primary ? `${(primary.metrics.accuracy * 100).toFixed(2)}%` : undefined, to: `/experiments?experiment=${experimentId}` },
    { label: 'Selected macro F1', value: primary?.metrics.macro_f1.toFixed(4), to: `/experiments?experiment=${experimentId}` },
  ];
  const rows = signal.data?.time_ms.map((time, i) => ({ time, ...Object.fromEntries(Object.entries(signal.data!.data).map(([ch, values]) => [ch, values[i]])) })) || [];
  return <><div className="page-heading"><div><h1>EOG INTENT COMMAND CENTRE</h1><p>Low-Latency EOG-Based Early Intent Detection for Eye Movements</p></div><Link className="button-link primary" to="/predictions">Run a prediction</Link></div>
    <div className="metric-strip">{metrics.map(metric => <Link to={metric.to} key={metric.label} className="metric"><span>{metric.label}</span><strong>{metric.value ?? 'Unavailable'}</strong></Link>)}</div>
    {(summary.error || list.error || detail.error) && <Notice message={summary.error || list.error || detail.error!} />}
    <ExperimentPicker entries={list.data?.experiments || []} value={experimentId} onChange={setExperimentId} />
    {detail.data && <Provenance experiment={detail.data} />}
    <JobsPanel />
    <div className="analysis-grid section"><div className="card"><div className="card-header"><div><h2>Recorded EOG · S1 / trial 0</h2><p className="muted">Raw outward phase · source sample order</p></div><Link to="/predictions?subject=S1&trial=0">Predict this trial</Link></div>{signal.error ? <Notice message={signal.error} /> : signal.loading ? <Loading /> : <Waveform rows={rows} channels={['0', '1', '2']} />}</div><Pipeline /></div>
    <div className="card section"><div className="card-header"><h2>Accuracy vs observation budget</h2><Link to={`/experiments?experiment=${experimentId}`}>Full evaluation</Link></div>{results.length ? <><AccuracyChart results={results} /><ResultTable results={results} experimentId={experimentId} /></> : <p className="muted">No completed metrics selected. Choose a completed experiment or run a job.</p>}</div>
    <p className="muted">Observation duration is not cue-to-decision latency. Results describe recorded-data experiments, not clinical or hardware validation.</p>
  </>;
}
