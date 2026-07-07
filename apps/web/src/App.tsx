import { useEffect, useMemo, useState } from 'react';

import { fetchFleetOverview, fetchInvestigationDetail, fetchInvestigationQueue } from './api';
import type { FleetOverview, InvestigationDetail, InvestigationItem, RiskLevel } from './types';
import './styles.css';

const flowStages = ['Detect', 'Triage', 'Investigate', 'Hypothesize', 'Act', 'Verify', 'Report'];

const riskLabels: Record<RiskLevel, string> = {
  healthy: 'Healthy',
  warning: 'Warning',
  critical: 'Critical',
  stale: 'Stale',
};

function metricValue(detail: InvestigationDetail | null, name: string): string {
  const metric = detail?.fleet_context.latest_metrics[name];
  if (!metric) return 'Unavailable';
  if (metric.unit === 'celsius') return `${metric.value.toFixed(1)}C`;
  if (metric.unit === 'percent') return `${metric.value.toFixed(1)}%`;
  return `${metric.value}`;
}

function priorityClass(priority: InvestigationItem['priority']): string {
  return `priority priority-${priority.toLowerCase()}`;
}

function riskClass(level: RiskLevel): string {
  return `risk risk-${level}`;
}

export default function App() {
  const [overview, setOverview] = useState<FleetOverview | null>(null);
  const [queue, setQueue] = useState<InvestigationItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<InvestigationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    Promise.all([fetchFleetOverview(), fetchInvestigationQueue()])
      .then(([fleetData, queueData]) => {
        if (!active) return;
        setOverview(fleetData);
        setQueue(queueData.items);
        setSelectedId(queueData.items[0]?.id ?? null);
        setError(null);
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof Error ? err.message : 'Unknown API error');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    let active = true;
    fetchInvestigationDetail(selectedId)
      .then((data) => {
        if (active) setDetail(data);
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof Error ? err.message : 'Unknown detail API error');
      });
    return () => {
      active = false;
    };
  }, [selectedId]);

  const selectedItem = useMemo(
    () => queue.find((item) => item.id === selectedId) ?? queue[0] ?? null,
    [queue, selectedId],
  );

  if (loading) {
    return (
      <main className="page">
        <p className="status">Loading investigations...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page">
        <h1>Quipu</h1>
        <p className="error">{error}</p>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="topbar">
        <div>
          <p className="eyebrow">Team workstation health investigator</p>
          <h1>Quipu</h1>
        </div>
        <p className="generated">Detect - triage - verify with evidence</p>
      </header>

      <section className="flow-rail" aria-label="DTIHAVR workflow">
        <p>Detect -&gt; Triage -&gt; Investigate -&gt; Hypothesize -&gt; Act -&gt; Verify -&gt; Report</p>
        <div>
          {flowStages.map((stage) => (
            <span
              aria-current={selectedItem?.stage === stage ? 'step' : undefined}
              className={selectedItem?.stage === stage ? 'active' : undefined}
              key={stage}
            >
              {stage}
            </span>
          ))}
        </div>
      </section>

      <section className="summary" aria-label="Fleet summary">
        <div><span>{overview?.summary.total ?? 0}</span><strong>Total</strong></div>
        <div><span>{overview?.summary.critical ?? 0}</span><strong>Critical</strong></div>
        <div><span>{overview?.summary.warning ?? 0}</span><strong>Warnings</strong></div>
        <div><span>{queue.length}</span><strong>Queue</strong></div>
      </section>

      <section className="investigation-layout">
        <aside className="panel queue-panel">
          <div className="panel-head">
            <h2>Investigation Queue</h2>
            <span>{queue.length} items</span>
          </div>
          <div className="queue-list">
            {queue.length === 0 ? (
              <p className="status">No active investigations.</p>
            ) : (
              queue.map((item) => (
                <button
                  className={item.id === selectedItem?.id ? 'queue-item selected' : 'queue-item'}
                  key={item.id}
                  onClick={() => setSelectedId(item.id)}
                  type="button"
                >
                  <span className={priorityClass(item.priority)}>{item.priority}</span>
                  <strong>{item.device_hostname}</strong>
                  <em>{item.why_now}</em>
                  <small>{item.next_step}</small>
                </button>
              ))
            )}
          </div>
        </aside>

        <section className="detail-grid">
          <article className="panel hero-panel">
            <div className="panel-head">
              <h2>{detail?.item.title ?? 'Select an investigation'}</h2>
              {detail && <span className={riskClass(detail.item.risk_level)}>{riskLabels[detail.item.risk_level]}</span>}
            </div>
            <p className="lead">{detail?.item.evidence ?? 'Choose an item from the investigation queue.'}</p>
            {detail && (
              <dl className="metric-strip">
                <div><dt>CPU</dt><dd>{metricValue(detail, 'cpu.package_temp_c')}</dd></div>
                <div><dt>Load</dt><dd>{metricValue(detail, 'cpu.load_1m')}</dd></div>
                <div><dt>NVMe</dt><dd>{metricValue(detail, 'nvme.temp_c')}</dd></div>
              </dl>
            )}
          </article>

          <article className="panel">
            <div className="panel-head">
              <h2>Evidence timeline</h2>
              <span>{detail?.timeline.length ?? 0} events</span>
            </div>
            <div className="timeline">
              {detail?.timeline.map((event) => (
                <div className="timeline-row" key={`${event.observed_at}-${event.category}-${event.summary}`}>
                  <time>{new Date(event.observed_at).toLocaleString()}</time>
                  <strong>{event.category} / {event.severity}</strong>
                  <p>{event.summary}</p>
                  {event.raw_ref && <code>{event.raw_ref}</code>}
                </div>
              ))}
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <h2>Top hypotheses</h2>
              <span>{detail?.hypotheses.length ?? 0}</span>
            </div>
            {detail?.hypotheses.map((hypothesis) => (
              <section className="hypothesis" key={hypothesis.category}>
                <strong>{hypothesis.title}</strong>
                <span>{hypothesis.category} / {hypothesis.confidence}</span>
                <p>{hypothesis.supporting_evidence[0]}</p>
                <p className="counter">{hypothesis.contradicting_evidence[0]}</p>
              </section>
            ))}
          </article>

          <article className="panel">
            <div className="panel-head">
              <h2>Action plan</h2>
              <span>{detail?.actions.length ?? 0}</span>
            </div>
            {detail?.actions.map((action) => (
              <div className="action" key={action.label}>
                <strong>{action.label}</strong>
                <p>{action.description}</p>
              </div>
            ))}
          </article>

          <article className="panel">
            <div className="panel-head">
              <h2>Verification</h2>
              <span>{detail?.verification.status ?? 'Pending'}</span>
            </div>
            <p className="lead">{detail?.verification.summary}</p>
            <div className="signal-list">
              {detail?.verification.signals.map((signal) => <span key={signal}>{signal}</span>)}
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <h2>Report</h2>
              <span>Draft</span>
            </div>
            <p className="lead">{detail?.report.summary}</p>
            <p className="next-step">{detail?.report.recommended_next_step}</p>
          </article>
        </section>
      </section>
    </main>
  );
}
