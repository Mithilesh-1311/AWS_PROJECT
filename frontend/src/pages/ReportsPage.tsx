import { useState } from 'react';
import { fetchResponse } from '../services/api';
import { useExperiment } from '../hooks/useExperiment';
import { ExperimentPicker, Provenance, ResultTable } from '../components/ExperimentPanels';
import { Loading, Notice } from '../components/ResearchPanels';

export default function ReportsPage() {
  const { list, detail, experimentId, setExperimentId } = useExperiment();
  const report = detail.data;
  const [exportError, setExportError] = useState('');
  async function exportReport(format: 'json' | 'csv' | 'html') {
    const preview = format === 'html' ? window.open('about:blank', '_blank') : null;
    if (preview) preview.opener = null;
    setExportError('');
    try {
      const response = await fetchResponse(`/v1/experiments/${encodeURIComponent(experimentId)}/export?format=${format}`);
      const url = URL.createObjectURL(await response.blob());
      if (preview) preview.location.replace(url);
      else {
        const link = document.createElement('a');
        link.href = url; link.download = `${experimentId}.${format}`; link.click();
      }
      window.setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (reason) {
      preview?.close();
      setExportError(reason instanceof Error ? reason.message : 'Export failed. Try again.');
    }
  }
  return <><div className="page-heading"><div><h1>Reports & provenance</h1><p>Export actual experiment results, configuration and source checksums.</p></div></div><ExperimentPicker entries={list.data?.experiments || []} value={experimentId} onChange={setExperimentId} />
    {(list.error || detail.error) && <Notice message={list.error || detail.error!} />}
    {exportError && <Notice message={exportError} />}
    {list.loading || detail.loading ? <Loading label="Loading experiment provenance" /> : report ? <><Provenance experiment={report} /><div className="controls-row">{(['json', 'csv', 'html'] as const).map(format => <button key={format} onClick={() => void exportReport(format)}>{format === 'html' ? 'Printable report' : `Export ${format.toUpperCase()}`}</button>)}</div>
      <div className="card"><h2>Experiment record</h2><dl className="timing-list"><div><dt>ID</dt><dd>{experimentId}</dd></div><div><dt>State</dt><dd>{report.status}</dd></div><div><dt>Source trials</dt><dd>{report.total_source_trials ?? 'Unavailable'}</dd></div><div><dt>Excluded trial/window pairs</dt><dd>{report.exclusion_count ?? 'Unavailable'}</dd></div><div><dt>Evaluation runtime</dt><dd>{report.runtime_seconds?.toFixed(2) ?? 'Unavailable'} s</dd></div><div><dt>Selection policy</dt><dd>{report.config.selection_policy}</dd></div></dl></div>
      <div className="card section"><h2>Measured results</h2><ResultTable results={report.results || []} experimentId={experimentId} /></div><details className="card"><summary>Full machine-readable manifest</summary><pre>{JSON.stringify(report, null, 2)}</pre></details></> : <div className="notice">No new experiments available. Run a real-data job from Overview.</div>}
  </>;
}
