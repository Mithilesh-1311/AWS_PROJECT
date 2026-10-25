import { useState, useEffect } from 'react';

export function useFetch<T>(fetcher: () => Promise<T>, deps: any[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetcher()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || 'Unknown error');
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, deps);

  return { data, loading, error, refetch: () => {
    setLoading(true);
    fetcher().then(setData).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }};
}
