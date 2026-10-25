import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { api } from './services/api';
import OverviewPage from './pages/OverviewPage';
import DatasetPage from './pages/DatasetPage';
import SignalPage from './pages/SignalPage';
import EarlyWindowPage from './pages/EarlyWindowPage';
import ExperimentsPage from './pages/ExperimentsPage';
import QualityPage from './pages/QualityPage';
import MethodologyPage from './pages/MethodologyPage';
import './index.css';

const NAV_ITEMS = [
  { path: '/', label: 'Overview', icon: '◈' },
  { path: '/dataset', label: 'Dataset', icon: '◉' },
  { path: '/signal', label: 'Signal Processing', icon: '∿' },
  { path: '/early-window', label: 'Early Window', icon: '⧗' },
  { path: '/experiments', label: 'Experiments', icon: '◎' },
  { path: '/quality', label: 'Data Quality', icon: '✓' },
  { path: '/methodology', label: 'Methodology', icon: '⊞' },
];

function Sidebar() {
  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <h2>EOG Intent</h2>
        <p>Early Saccade Direction Prediction</p>
      </div>
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            end={item.path === '/'}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <BackendStatus />
    </div>
  );
}

function BackendStatus() {
  const [status, setStatus] = useState<'online' | 'offline'>('offline');
  useEffect(() => {
    const check = () => {
      api.health()
        .then(() => setStatus('online'))
        .catch(() => setStatus('offline'));
    };
    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="sidebar-status">
      <span className={`status-dot ${status}`}></span>
      Backend {status}
    </div>
  );
}

function Topbar() {
  const location = useLocation();
  const current = NAV_ITEMS.find(n => n.path === location.pathname) || NAV_ITEMS[0];
  return (
    <div className="topbar">
      <span className="topbar-title">
        Low-Latency EOG-Based Early Intent Detection — {current.label}
      </span>
      <div className="topbar-status">
        <span>16-Channel Isotropic EOG System</span>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <div className="main-content">
          <Topbar />
          <div className="page-content">
            <Routes>
              <Route path="/" element={<OverviewPage />} />
              <Route path="/dataset" element={<DatasetPage />} />
              <Route path="/signal" element={<SignalPage />} />
              <Route path="/early-window" element={<EarlyWindowPage />} />
              <Route path="/experiments" element={<ExperimentsPage />} />
              <Route path="/quality" element={<QualityPage />} />
              <Route path="/methodology" element={<MethodologyPage />} />
            </Routes>
          </div>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
