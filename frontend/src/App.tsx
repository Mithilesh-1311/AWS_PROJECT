import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { useEffect, useRef, useState, lazy, Suspense } from 'react';
import { Activity, Database, SlidersHorizontal, Timer, Target, Radio, BarChart3, ShieldCheck, Workflow, FileText, Menu, X } from 'lucide-react';
import { api, remoteApi } from './services/api';
import AccessGate from './components/AccessGate';
import type { Readiness } from './services/types';
import { Loading } from './components/RequestState';
import './index.css';
const Overview = lazy(() => import('./pages/OverviewPage'));
const Dataset = lazy(() => import('./pages/DatasetPage'));
const Signal = lazy(() => import('./pages/SignalPage'));
const EarlyWindow = lazy(() => import('./pages/EarlyWindowPage'));
const Predictions = lazy(() => import('./pages/PredictionsPage'));
const Replay = lazy(() => import('./pages/ReplayPage'));
const Evaluation = lazy(() => import('./pages/EvaluationPage'));
const Quality = lazy(() => import('./pages/QualityPage'));
const Methodology = lazy(() => import('./pages/MethodologyPage'));
const Reports = lazy(() => import('./pages/ReportsPage'));
const navigation = [
  { path: '/', label: 'Overview', icon: Activity }, { path: '/dataset', label: 'Dataset Explorer', icon: Database },
  { path: '/signal', label: 'Signal Processing', icon: SlidersHorizontal }, { path: '/early-window', label: 'Early Windows', icon: Timer },
  { path: '/predictions', label: 'Predictions', icon: Target }, { path: '/replay', label: 'Live Replay', icon: Radio },
  { path: '/experiments', label: 'Model Evaluation', icon: BarChart3 }, { path: '/quality', label: 'Data Quality', icon: ShieldCheck },
  { path: '/methodology', label: 'Methodology', icon: Workflow }, { path: '/reports', label: 'Reports', icon: FileText },
];
function Navigation({ close }: { close?: () => void }) {
  return <><div className="sidebar-logo"><Activity size={23} aria-hidden="true" /><div><strong>EOG Intent</strong><span>RESEARCH WORKSPACE</span></div></div><nav className="sidebar-nav" aria-label="Main navigation">{navigation.map(({ path, label, icon: Icon }) => <NavLink key={path} to={path} end={path === '/'} onClick={close} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><Icon size={16} aria-hidden="true" />{label}</NavLink>)}</nav><div className="sidebar-status"><span className="badge badge-info">RECORDED EOG</span><p>Research use · eight directions<br />No live sensor attached</p></div></>;
}
function Shell() {
  const location = useLocation();
  const dialog = useRef<HTMLDialogElement>(null);
  const [ready, setReady] = useState<Readiness | null>(null);
  const [connection, setConnection] = useState('checking');
  useEffect(() => {
    const controller = new AbortController();
    const check = () => api.ready(controller.signal).then(result => { setReady(result); setConnection('connected'); }).catch(() => { if (!controller.signal.aborted) { setReady(null); setConnection('disconnected'); } });
    void check(); const interval = setInterval(check, 10000);
    return () => { controller.abort(); clearInterval(interval); };
  }, []);
  return <div className="app-layout"><a href="#main" className="skip-link">Skip to content</a><aside className="sidebar desktop-nav"><Navigation /></aside>
    <dialog ref={dialog} className="navigation-dialog" aria-label="Navigation"><button className="drawer-close" aria-label="Close navigation" onClick={() => dialog.current?.close()}><X size={18} /></button><Navigation close={() => dialog.current?.close()} /></dialog>
    <div className="main-content"><header className="topbar"><div className="brand-line"><button className="mobile-menu" aria-label="Open navigation" onClick={() => dialog.current?.showModal()}><Menu size={20} /></button><strong>EOG Intent</strong><span>EARLY EYE-MOVEMENT INTELLIGENCE</span></div><div className="topbar-status">{(['dataset', 'model', 'worker'] as const).map(key => <span key={key} className={ready?.[key] ? 'status-ready' : 'status-unavailable'}><i aria-hidden="true" />{key} {ready ? ready[key] ? 'ready' : 'unavailable' : 'unknown'}</span>)}</div></header>
      <main id="main" className="page-content" key={location.pathname}><Suspense fallback={<Loading label="Loading research workspace" />}><Routes><Route path="/" element={<Overview />} /><Route path="/dataset" element={<Dataset />} /><Route path="/signal" element={<Signal />} /><Route path="/early-window" element={<EarlyWindow />} /><Route path="/predictions" element={<Predictions />} /><Route path="/replay" element={<Replay />} /><Route path="/experiments" element={<Evaluation />} /><Route path="/quality" element={<Quality />} /><Route path="/methodology" element={<Methodology />} /><Route path="/reports" element={<Reports />} /><Route path="*" element={<div className="notice">Page not found. Use the navigation to choose a research tool.</div>} /></Routes></Suspense></main>
      <footer className="app-footer"><span>API {connection}</span>{remoteApi && <button onClick={() => { sessionStorage.removeItem('eog-access-token'); window.dispatchEvent(new Event('eog-auth-required')); }}>Sign out</button>}<span>Application {ready?.version ?? 'version unavailable'} · build {import.meta.env.VITE_BUILD_ID || 'local'}</span></footer></div></div>;
}
export default function App() { return <AccessGate><BrowserRouter><Shell /></BrowserRouter></AccessGate>; }
