import { useState, useEffect, useEffectEvent } from 'react';

export function useFetch<T>(fetcher: (signal: AbortSignal) => Promise<T>, deps: readonly unknown[] = []) {
  const [revision, setRevision] = useState(0);
  const key = JSON.stringify([deps, revision]);
  const [state, setState] = useState<{ key: string; data: T | null; error: string | null } | null>(null);
  const load = useEffectEvent(fetcher);
  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal).then(data => {
      if (!controller.signal.aborted) setState({ key, data, error: null });
    }).catch(error => {
      if (!controller.signal.aborted) setState({ key, data: null, error: error instanceof Error ? error.message : 'Request failed' });
    });
    return () => controller.abort();
  }, [key]);
  const current = state?.key === key ? state : null;
  return { data: current?.data ?? null, loading: current === null, error: current?.error ?? null,
    refetch: () => setRevision(value => value + 1) };
}
