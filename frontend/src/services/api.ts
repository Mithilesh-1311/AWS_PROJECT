import type { Health, Readiness, DatasetSummary, Subject, Trial, SignalData, Onset, Processing, EarlyWindow, QualityReport, LegacyExperiment, ExperimentSummary, Experiment, ModelRecord, Prediction, Job } from './types';

export const API_BASE = (import.meta.env.VITE_API_BASE || '/api').replace(/\/$/, '');
export const remoteApi = new URL(API_BASE, window.location.href).origin !== window.location.origin;
export const accessToken = () => sessionStorage.getItem('eog-access-token') || '';
export function replayProtocols() {
  return accessToken() ? ['eog-replay', `eog-token.${accessToken()}`] : [];
}
export async function fetchResponse(url: string, signal?: AbortSignal, body?: unknown): Promise<Response> {
  const timeout = AbortSignal.timeout(30000);
  const res = await fetch(`${API_BASE}${url}`, {
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    headers: { ...(accessToken() ? { Authorization: `Bearer ${accessToken()}` } : {}), ...(body === undefined ? {} : { 'Content-Type': 'application/json' }) },
    ...(body === undefined ? {} : { method: 'POST', body: JSON.stringify(body) }),
  });
  if (!res.ok) {
    if (res.status === 403 && remoteApi) {
      sessionStorage.removeItem('eog-access-token');
      window.dispatchEvent(new Event('eog-auth-required'));
    }
    const data: { detail?: unknown } = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === 'string' ? data.detail : `Request failed (${res.status}). Check the selected inputs and service connection.`);
  }
  return res;
}
export async function fetchJson<T>(url: string, signal?: AbortSignal, body?: unknown): Promise<T> {
  return (await fetchResponse(url, signal, body)).json() as Promise<T>;
}
const query = (params?: Record<string, string>) => params ? '?' + new URLSearchParams(params) : '';
const id = encodeURIComponent;
export const api = {
  health: (s?: AbortSignal) => fetchJson<Health>('/health', s),
  ready: (s?: AbortSignal) => fetchJson<Readiness>('/ready', s),
  datasetSummary: (s?: AbortSignal) => fetchJson<DatasetSummary>('/dataset/summary', s),
  subjects: (s?: AbortSignal) => fetchJson<{ subjects: Subject[] }>('/subjects', s),
  subjectSummary: (subject: string, s?: AbortSignal) => fetchJson<Subject>(`/subjects/${id(subject)}/summary`, s),
  trials: (subject: string, s?: AbortSignal) => fetchJson<{ subject_id: string; n_trials: number; trials: Trial[] }>(`/subjects/${id(subject)}/trials`, s),
  trialSignal: (subject: string, trial: number, params?: Record<string, string>, s?: AbortSignal) => fetchJson<SignalData>(`/subjects/${id(subject)}/trials/${trial}/signal${query(params)}`, s),
  trialOnset: (subject: string, trial: number, s?: AbortSignal) => fetchJson<Onset>(`/subjects/${id(subject)}/trials/${trial}/onset`, s),
  earlyWindow: (subject: string, trial: number, ms: number, alignment: string, s?: AbortSignal) => fetchJson<EarlyWindow>(`/subjects/${id(subject)}/trials/${trial}/early-window?window_ms=${ms}&alignment=${id(alignment)}`, s),
  signalProcessing: (subject: string, trial: number, params: Record<string, string>, s?: AbortSignal) => fetchJson<Processing>(`/subjects/${id(subject)}/trials/${trial}/processing${query(params)}`, s),
  experiments: (s?: AbortSignal) => fetchJson<{ experiments: Omit<LegacyExperiment, 'window_results'>[] }>('/experiments', s),
  experimentDetail: (experiment: string, s?: AbortSignal) => fetchJson<LegacyExperiment>(`/experiments/${id(experiment)}`, s),
  latestResults: (s?: AbortSignal) => fetchJson<LegacyExperiment>('/experiments/latest/results', s),
  dataQuality: (s?: AbortSignal) => fetchJson<QualityReport>('/data-quality', s),
  models: (s?: AbortSignal) => fetchJson<{ models: ModelRecord[]; active_model_id: string | null }>('/v1/models', s),
  activate: (model: string) => fetchJson<{ active_model_id: string }>(`/v1/models/${id(model)}/activate`, undefined, {}),
  predict: (subject: string, trial: number, model?: string, s?: AbortSignal) => fetchJson<Prediction>('/v1/predictions', s, { subject_id: subject, trial_id: trial, model_id: model || null }),
  researchExperiments: (s?: AbortSignal) => fetchJson<{ experiments: ExperimentSummary[] }>('/v1/experiments', s),
  researchExperiment: (experiment: string, s?: AbortSignal) => fetchJson<Experiment>(`/v1/experiments/${id(experiment)}`, s),
  jobs: (s?: AbortSignal) => fetchJson<{ jobs: Job[]; worker_ready: boolean }>('/v1/jobs', s),
  createJob: () => fetchJson<Job>('/v1/jobs', undefined, { subjects: ['S1', 'S2', 'S3'], models: ['logistic_regression'], windows: [100], evaluation: 'holdout', smoke: true }),
  cancelJob: (job: string) => fetchJson<Job>(`/v1/jobs/${id(job)}/cancel`, undefined, {}),
};
export function replayUrl() {
  const url = new URL(`${API_BASE}/v1/replay`, window.location.href);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  return url.toString();
}
