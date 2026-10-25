import { useSearchParams } from 'react-router-dom';

export function useTrialSelection() {
  const [params, setParams] = useSearchParams();
  const subjectId = /^S(?:[1-9]|1[0-4])$/.test(params.get('subject') || '') ? params.get('subject')! : 'S1';
  const parsed = Number(params.get('trial') || 0);
  const trialId = Number.isInteger(parsed) && parsed >= 0 && parsed < 288 ? parsed : 0;
  const setSubjectId = (subject: string) => setParams(previous => { const next = new URLSearchParams(previous); next.set('subject', subject); next.set('trial', '0'); return next; });
  const setTrialId = (trial: number) => setParams(previous => { const next = new URLSearchParams(previous); next.set('trial', String(trial)); return next; });
  return { subjectId, trialId, setSubjectId, setTrialId };
}
