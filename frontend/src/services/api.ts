const API_BASE = 'http://localhost:8000/api';

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  health: () => fetchJson<any>('/health'),
  datasetSummary: () => fetchJson<any>('/dataset/summary'),
  subjects: () => fetchJson<any>('/subjects'),
  subjectSummary: (id: string) => fetchJson<any>(`/subjects/${id}/summary`),
  trials: (subjectId: string) => fetchJson<any>(`/subjects/${subjectId}/trials`),
  trialSignal: (subjectId: string, trialId: number, params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchJson<any>(`/subjects/${subjectId}/trials/${trialId}/signal${qs}`);
  },
  trialOnset: (subjectId: string, trialId: number) =>
    fetchJson<any>(`/subjects/${subjectId}/trials/${trialId}/onset`),
  earlyWindow: (subjectId: string, trialId: number, windowMs: number, alignment: string) =>
    fetchJson<any>(`/subjects/${subjectId}/trials/${trialId}/early-window?window_ms=${windowMs}&alignment=${alignment}`),
  signalProcessing: (subjectId: string, trialId: number, params: Record<string, string>) => {
    const qs = '?' + new URLSearchParams(params).toString();
    return fetchJson<any>(`/subjects/${subjectId}/trials/${trialId}/processing${qs}`);
  },
  experiments: () => fetchJson<any>('/experiments'),
  experimentDetail: (id: string) => fetchJson<any>(`/experiments/${id}`),
  latestResults: () => fetchJson<any>('/experiments/latest/results'),
  dataQuality: () => fetchJson<any>('/data-quality'),
};
