import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import type { Prediction } from '../services/types';
import { useFetch } from '../hooks/useFetch';
import { useTrialSelection } from '../hooks/useTrialSelection';
import { TrialControls, Notice, Loading, Waveform, PredictionView } from '../components/ResearchPanels';

export default function PredictionsPage() {
  const selection = useTrialSelection();
  const { subjectId, trialId } = selection;
  const models = useFetch(api.models);
  const [modelChoice, setModelChoice] = useState('');
  const modelId = modelChoice || models.data?.active_model_id || '';
  const signal = useFetch(abort => api.trialSignal(subjectId, trialId, { channels: '0,1,2,3', phase: 'outward' }, abort), [subjectId, trialId]);
  const [result, setResult] = useState<{ key: string; prediction: Prediction } | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const request = useRef<AbortController | null>(null);
  const key = `${subjectId}:${trialId}:${modelId}`;
  useEffect(() => () => request.current?.abort(), []);
  useEffect(() => { request.current?.abort(); }, [key]);
  async function predict() {
    request.current?.abort();
    const controller = new AbortController(); request.current = controller;
    setPending(true); setError(null);
    try { const prediction = await api.predict(subjectId, trialId, modelId, controller.signal); if (!controller.signal.aborted) setResult({ key, prediction }); }
    catch (e) { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Prediction failed'); }
    finally { if (request.current === controller) setPending(false); }
  }
  const prediction = result?.key === key ? result.prediction : null;
  const rows = signal.data?.time_ms.map((time, i) => ({ time, ...Object.fromEntries(Object.entries(signal.data!.data).map(([ch, values]) => [ch, values[i]])) })) || [];
  return <><div className="page-heading"><div><h1>Predictions</h1><p>Run the saved model on a real early observation window.</p></div><span className="badge badge-info">CAUSAL RECORDED TRIAL</span></div>
    <TrialControls {...selection} />
    <div className="controls-row"><label className="control-group">Serving model<select value={modelId} onChange={e => setModelChoice(e.target.value)}><option value="">Select an available model</option>{models.data?.models.map(model => <option key={model.model_id} value={model.model_id} disabled={!model.ready}>{model.ready ? '' : 'INCOMPATIBLE / '}{model.window_ms} ms · {model.model_id.slice(0, 8)}</option>)}</select></label><button className="primary" onClick={predict} disabled={pending || !modelId}>{pending ? 'Predicting…' : 'Predict direction'}</button><Link to={`/replay?subject=${subjectId}&trial=${trialId}`}>Replay this trial</Link></div>
    {!models.loading && !models.data?.models.some(model => model.ready) && <div className="notice">No compatible model. Run the serving training command in the experiment guide, then activate its model.</div>}
    {(error || signal.error || models.error) && <Notice message={error || signal.error || models.error!} />}
    <div className="analysis-grid"><div className="card"><h2>Recorded EOG · {subjectId} / trial {trialId}</h2>{signal.loading ? <Loading /> : <Waveform rows={rows} channels={['0', '1', '2', '3']} window={prediction?.state === 'predicted' ? prediction.window : undefined} />}</div>
      {prediction ? <PredictionView prediction={prediction} /> : <div className="card empty-state"><h2>Awaiting prediction</h2><p>Choose a trial and run the model. Calibration and onset confirmation must finish before a prediction is available.</p><p className="muted">Target labels are used only for evaluation. They are not model inputs.</p></div>}</div>
  </>;
}
