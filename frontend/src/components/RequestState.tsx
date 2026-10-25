export function Notice({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="error-box" role="alert"><span>{message}</span>{retry && <button onClick={retry}>Retry request</button>}</div>;
}

export function Loading({ label = 'Loading recorded data' }: { label?: string }) {
  return <div className="loading-state" role="status"><span className="loading-indicator" />{label}</div>;
}

