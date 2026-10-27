import { useEffect, useState, type ReactNode, type FormEvent } from 'react';
import { accessToken, api, remoteApi } from '../services/api';

export default function AccessGate({ children }: { children: ReactNode }) {
  const [authenticated, setAuthenticated] = useState(!remoteApi || !!accessToken());
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const signOut = () => { setAuthenticated(false); setToken(''); };
    window.addEventListener('eog-auth-required', signOut);
    return () => window.removeEventListener('eog-auth-required', signOut);
  }, []);
  async function signIn(event: FormEvent) {
    event.preventDefault();
    setBusy(true); setError('');
    sessionStorage.setItem('eog-access-token', token.trim());
    try {
      await api.models();
      setToken(''); setAuthenticated(true);
    } catch (reason) {
      sessionStorage.removeItem('eog-access-token');
      setError(reason instanceof Error ? reason.message : 'Sign-in failed. Try again.');
    } finally { setBusy(false); }
  }
  if (authenticated) return children;
  return <main className="access-gate"><form className="card" onSubmit={signIn}>
    <h1>Sign in to EOG Intent</h1><p>Enter the access token provided by the workspace owner.</p>
    <label htmlFor="access-token">Access token</label>
    <input id="access-token" type="password" autoComplete="off" required minLength={32} maxLength={256} value={token} onChange={event => setToken(event.target.value)} />
    {error && <p role="alert">{error}</p>}
    <button className="primary" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
  </form></main>;
}
