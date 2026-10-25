import { useSearchParams } from 'react-router-dom';
import { useFetch } from './useFetch';
import { api } from '../services/api';

export function useExperiment() {
  const [params, setParams] = useSearchParams();
  const list = useFetch(api.researchExperiments);
  const completed = list.data?.experiments.filter(e => e.status === 'complete') || [];
  const preferred = [...completed].sort((a, b) => Number(a.config.smoke) - Number(b.config.smoke) || b.timestamp.localeCompare(a.timestamp));
  const experimentId = params.get('experiment') || preferred[0]?.experiment_id || '';
  const detail = useFetch(signal => experimentId ? api.researchExperiment(experimentId, signal) : Promise.resolve(null), [experimentId]);
  return { list, detail, experimentId, setExperimentId: (id: string) => setParams(previous => { const next = new URLSearchParams(previous); next.set('experiment', id); return next; }) };
}
