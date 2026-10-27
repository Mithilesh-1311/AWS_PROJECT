import { useEffect, useRef, useState } from 'react';
import { replayUrl, replayProtocols, api } from '../services/api';
import type { Predicted, ReplayEvent } from '../services/types';
import { useFetch } from '../hooks/useFetch';
import { useTrialSelection } from '../hooks/useTrialSelection';
import { TrialControls, Notice, Waveform, PredictionView } from '../components/ResearchPanels';

export default function ReplayPage() {
  const selection = useTrialSelection();
  const registry = useFetch(api.models);
  const [speed, setSpeed] = useState(1);
  const [channelsText, setChannelsText] = useState('0,1,2,3');
  const [state, setState] = useState('disconnected');
  const [error, setError] = useState<string | null>(null);
  const [rows, setRows] = useState<Record<string, number>[]>([]);
  const [prediction, setPrediction] = useState<Predicted | null>(null);
  const [sample, setSample] = useState(0);
  const [total, setTotal] = useState<number | null>(null);
  const socket = useRef<WebSocket | null>(null);
  const expected = useRef({ sample: 0, sequence: 0 });
  const key = `${selection.subjectId}:${selection.trialId}`;
  useEffect(() => () => { socket.current?.close(); }, [key]);
  const channels = channelsText.split(',').map(c => c.trim());

  function connect() {
    socket.current?.close();
    const selected = channels.map(Number);
    if (!selected.length || selected.length > 16 || selected.some(n => !Number.isInteger(n) || n < 0 || n >= 16) || new Set(selected).size !== selected.length) { setError('Choose distinct channels from 0 to 15.'); return; }
    setError(null); setRows([]); setPrediction(null); setSample(0); setTotal(null);
    expected.current = { sample: 0, sequence: 0 };
    const ws = new WebSocket(replayUrl(), replayProtocols()); socket.current = ws; setState('connecting');
    ws.onopen = () => { if (socket.current !== ws) return; ws.send(JSON.stringify({ subject_id: selection.subjectId, trial_id: selection.trialId, model_id: registry.data?.active_model_id, speed, channels: selected, chunk_size: 16 })); setState('playing'); };
    ws.onmessage = event => {
      if (socket.current !== ws) return;
      let data: ReplayEvent;
      try { data = JSON.parse(event.data) as ReplayEvent; } catch { setError('Invalid replay message. Reconnect to reset the session.'); ws.close(); return; }
      if (data.type === 'metadata') setTotal(data.n_samples ?? null);
      if (data.type === 'error') { setError(data.message || 'Replay failed'); ws.close(); }
      if (data.type === 'reset') { expected.current = { sample: 0, sequence: 0 }; setRows([]); setPrediction(null); setSample(0); }
      if (data.type === 'complete') { setState(data.state || 'complete'); if (data.evaluation) setPrediction(previous => previous ? { ...previous, evaluation: data.evaluation } : null); }
      if (data.type !== 'chunk') return;
      if (data.start_sample !== expected.current.sample || data.sequence !== expected.current.sequence || data.end_sample === undefined || !data.data) { setError('Sample gap or sequence error. Reconnect starts a clean session.'); ws.close(); return; }
      const values = data.data;
      const chunkRows = Array.from({ length: data.end_sample - data.start_sample }, (_, i) => ({ time: (data.start_sample! + i) / 256 * 1000, ...Object.fromEntries(Object.entries(values).map(([ch, v]) => [ch, v[i]])) }));
      expected.current = { sample: data.end_sample, sequence: data.sequence! + 1 };
      setRows(previous => [...previous, ...chunkRows].slice(-512)); setSample(data.end_sample);
      if (data.prediction) setPrediction(data.prediction);
    };
    ws.onerror = () => { if (socket.current === ws) setError('Replay connection failed. Check the backend and reconnect.'); };
    ws.onclose = () => { if (socket.current === ws) setState('disconnected'); };
  }
  function command(action: string, value?: number) {
    if (socket.current?.readyState !== WebSocket.OPEN) { setError('Connect to replay first.'); return; }
    socket.current.send(JSON.stringify({ action, value }));
    if (action === 'pause') setState('paused');
    if (action === 'play') setState('playing');
  }
  return <><div className="page-heading"><div><h1>Live Replay</h1><p>Server-side causal processing of recorded EOG chunks.</p></div><span className="badge badge-warning">RECORDED DATA REPLAY</span></div>
    <TrialControls {...selection} />
    <div className="controls-row"><label className="control-group">Playback speed<select value={speed} onChange={e => { const value = Number(e.target.value); setSpeed(value); if (socket.current?.readyState === WebSocket.OPEN) command('speed', value); }}>{[.25, .5, 1, 2, 4, 8].map(value => <option key={value} value={value}>{value}×</option>)}</select></label>
      <label className="control-group">Display channels<input value={channelsText} onChange={e => setChannelsText(e.target.value)} disabled={state === 'playing' || state === 'paused'} /></label>
      <button className="primary" onClick={connect} disabled={!registry.data?.active_model_id}>Connect / restart</button><button onClick={() => command(state === 'paused' ? 'play' : 'pause')} disabled={!['playing', 'paused'].includes(state)}>{state === 'paused' ? 'Play' : 'Pause'}</button><button onClick={() => command('reset')} disabled={state === 'disconnected' || state === 'connecting'}>Reset trial</button><button onClick={() => socket.current?.close()} disabled={state === 'disconnected'}>Disconnect</button></div>
    <div className="evidence-strip"><span>Status <strong>{state}</strong></span><span>Received <strong>{sample} / {total ?? '—'} samples</strong></span><span>Sampling <strong>256 Hz</strong></span><span>Client buffer <strong>512 samples maximum</strong></span></div>
    {(error || registry.error) && <Notice message={error || registry.error!} />}
    {!registry.loading && !registry.data?.active_model_id && <div className="notice">No active model. Train and activate a serving model before replay.</div>}
    <div className="analysis-grid"><div className="card"><h2>EOG stream · {selection.subjectId} / {selection.trialId}</h2><Waveform rows={rows} channels={channels} window={prediction?.window} /><p className="muted">Speed changes playback scheduling only. Source sample timing remains unchanged. Reconnection starts from the cue; target labels appear as evaluation metadata after replay.</p></div>{prediction ? <PredictionView prediction={prediction} /> : <div className="card empty-state"><h2>Awaiting confirmed window</h2><p>Calibration → sustained onset crossing → complete observation window → model inference.</p>{state === 'abstained' && <p className="notice">No eligible window in this trial. Select another recorded trial.</p>}</div>}</div>
  </>;
}
