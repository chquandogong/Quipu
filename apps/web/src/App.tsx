import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import {
  Activity,
  Bot,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  ExternalLink,
  Gauge,
  MousePointer2,
  ShieldCheck,
  Thermometer,
  UserRound,
} from 'lucide-react';

import { fetchFleetOverview, fetchInvestigationDetail, fetchInvestigationQueue, recordIntervention } from './api';
import type { FleetOverview, InvestigationDetail, InvestigationItem, RiskLevel, VerificationResult } from './types';
import './styles.css';

const flowStages = ['Detect', 'Triage', 'Investigate', 'Hypothesize', 'Act', 'Verify', 'Report'];

const makerImages = [
  {
    title: 'Physical AI systems',
    src: 'https://raw.githubusercontent.com/chquandogong/CHENGHAO-QUAN/gh-pages/chenghao_intro_assets/physical_ai_robotics_hero.png',
    caption: 'Robotics field context',
  },
  {
    title: 'Creator profile',
    src: 'https://raw.githubusercontent.com/chquandogong/CHENGHAO-QUAN/gh-pages/downloads/chenghao_physical_ai_self_intro.png',
    caption: 'Public portfolio snapshot',
  },
  {
    title: 'Dogu public site',
    src: 'https://cdn.imweb.me/upload/S202302215d855936bf226/5a39a0539f5c0.png',
    caption: 'MAKING THE WORLD SAFER',
  },
];

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

function verificationStatusLabel(status: VerificationResult['status']): string {
  return {
    helped: 'Helped',
    worse: 'Worse',
    unclear: 'Unclear',
    insufficient_data: 'Needs data',
  }[status];
}

function verificationClass(status: VerificationResult['status']): string {
  return `verification-badge verification-${status.replace('_', '-')}`;
}

function VerificationResultView({ result }: { result: VerificationResult }) {
  return (
    <div className="verification-result">
      <div className="verification-result-head">
        <span className={verificationClass(result.status)}>{verificationStatusLabel(result.status)}</span>
        <small>{result.window_minutes} min window</small>
      </div>
      <p>{result.summary}</p>
      <div className="comparison-list">
        {result.checks.map((check) => (
          <div className="comparison-row" key={check.name}>
            <strong>{check.name}</strong>
            <span>{check.before ?? 'Missing'} {'->'} {check.after ?? 'Missing'}</span>
            <em>{check.delta ?? check.verdict}</em>
          </div>
        ))}
      </div>
    </div>
  );
}

function scrollToPanel(panelId: string) {
  const panel = document.getElementById(panelId);
  panel?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  if (panel instanceof HTMLElement) {
    panel.focus({ preventScroll: true });
  }
}

export default function App() {
  const [overview, setOverview] = useState<FleetOverview | null>(null);
  const [queue, setQueue] = useState<InvestigationItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<InvestigationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [interventionLabel, setInterventionLabel] = useState('');
  const [interventionDescription, setInterventionDescription] = useState('');
  const [recordingIntervention, setRecordingIntervention] = useState(false);
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
  const latestVerificationResult = detail?.interventions[detail.interventions.length - 1]?.verification_result;
  const nextAction = detail?.actions[0];
  const primaryEvidence = detail?.timeline[0]?.summary ?? detail?.item.evidence ?? 'Select a queue item to inspect evidence.';
  const verificationLabel = detail?.verification.status ?? 'Pending';
  const verificationSummary = detail?.verification.summary ?? 'Record an intervention before verification.';

  async function handleRecordIntervention(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedId || !detail || !interventionLabel.trim() || !interventionDescription.trim()) return;
    setRecordingIntervention(true);
    try {
      const created = await recordIntervention(selectedId, {
        label: interventionLabel,
        description: interventionDescription,
        expected_effect: detail.actions[0]?.description ?? null,
        recorded_at: new Date().toISOString(),
      });
      setDetail({
        ...detail,
        interventions: [...detail.interventions, created],
        verification: {
          ...detail.verification,
          status: 'Waiting for after window',
          summary: 'Intervention recorded. Compare the next observation window before concluding it helped.',
        },
      });
      setInterventionLabel('');
      setInterventionDescription('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unknown intervention API error');
    } finally {
      setRecordingIntervention(false);
    }
  }

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

      <section className="maker-band" aria-label="Creator and reference visuals">
        <div className="maker-copy">
          <span><UserRound aria-hidden="true" /> Made by</span>
          <strong>Dr. 권성호 (QUAN CHENGHAO)</strong>
          <p>Dogu Robotics · Dogu X · Physical AI</p>
          <a href="https://github.com/chquandogong/CHENGHAO-QUAN" target="_blank" rel="noreferrer">
            <ExternalLink aria-hidden="true" />
            Creator profile
          </a>
        </div>
        <div className="visual-carousel" aria-label="Reference carousel">
          {makerImages.map((image) => (
            <figure className="visual-slide" key={image.title}>
              <img alt={image.title} loading="lazy" src={image.src} />
              <figcaption>
                <strong>{image.title}</strong>
                <span>{image.caption}</span>
              </figcaption>
            </figure>
          ))}
        </div>
        <div className="signal-turntable" aria-label="Signal turntable">
          <div>
            <Thermometer aria-hidden="true" />
            <span>Thermal</span>
          </div>
          <div>
            <Activity aria-hidden="true" />
            <span>Load</span>
          </div>
          <div>
            <ShieldCheck aria-hidden="true" />
            <span>Events</span>
          </div>
          <div>
            <Bot aria-hidden="true" />
            <span>Fleet</span>
          </div>
        </div>
      </section>

      <section className="summary" aria-label="Fleet summary">
        <div><span>{overview?.summary.total ?? 0}</span><strong>Total</strong></div>
        <div><span>{overview?.summary.critical ?? 0}</span><strong>Critical</strong></div>
        <div><span>{overview?.summary.warning ?? 0}</span><strong>Warnings</strong></div>
        <div><span>{queue.length}</span><strong>Queue</strong></div>
      </section>

      <section className="focus-board" aria-label="Current investigation focus">
        <article className="focus-card focus-primary">
          <span><Thermometer aria-hidden="true" /> Look first</span>
          <strong>{detail?.item.title ?? selectedItem?.title ?? 'No active investigation'}</strong>
          <p>{primaryEvidence}</p>
          <button onClick={() => scrollToPanel('evidence-panel')} type="button">
            <MousePointer2 aria-hidden="true" />
            Review evidence
          </button>
        </article>
        <article className="focus-card">
          <span><ChevronRight aria-hidden="true" /> Next action</span>
          <strong>{nextAction?.label ?? selectedItem?.next_step ?? 'Select a queue item'}</strong>
          <p>{nextAction?.description ?? selectedItem?.next_step ?? 'Choose an investigation before recording action.'}</p>
          <button onClick={() => scrollToPanel('action-plan')} type="button">
            <ClipboardCheck aria-hidden="true" />
            Record action
          </button>
        </article>
        <article className="focus-card">
          <span><CheckCircle2 aria-hidden="true" /> Verification</span>
          <strong>{verificationLabel}</strong>
          <p>{verificationSummary}</p>
          <button onClick={() => scrollToPanel('verification-panel')} type="button">
            <Gauge aria-hidden="true" />
            Verify result
          </button>
        </article>
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

          <article className="panel collapsible-panel" id="evidence-panel" tabIndex={-1}>
            <div className="panel-head">
              <h2>Evidence timeline</h2>
              <span>{detail?.timeline.length ?? 0} events</span>
            </div>
            <p className="panel-summary">{detail?.timeline[0]?.summary ?? 'No events selected.'}</p>
            <div className="panel-body timeline">
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

          <article className="panel collapsible-panel" id="hypotheses-panel" tabIndex={-1}>
            <div className="panel-head">
              <h2>Top hypotheses</h2>
              <span>{detail?.hypotheses.length ?? 0}</span>
            </div>
            <p className="panel-summary">{detail?.hypotheses[0]?.title ?? 'No hypotheses yet.'}</p>
            <div className="panel-body">
              {detail?.hypotheses.map((hypothesis) => (
                <section className="hypothesis" key={hypothesis.category}>
                  <strong>{hypothesis.title}</strong>
                  <span>{hypothesis.category} / {hypothesis.confidence}</span>
                  <p>{hypothesis.supporting_evidence[0]}</p>
                  <p className="counter">{hypothesis.contradicting_evidence[0]}</p>
                </section>
              ))}
            </div>
          </article>

          <article className="panel collapsible-panel action-panel" id="action-plan" tabIndex={-1}>
            <div className="panel-head">
              <h2>Action plan</h2>
              <span>{detail?.actions.length ?? 0}</span>
            </div>
            <p className="panel-summary">{nextAction?.description ?? 'No action selected.'}</p>
            <div className="panel-body">
              {detail?.actions.map((action) => (
                <div className="action" key={action.label}>
                  <strong>{action.label}</strong>
                  <p>{action.description}</p>
                </div>
              ))}
              {detail && (
                <form className="intervention-form" onSubmit={handleRecordIntervention}>
                  <label>
                    Intervention label
                    <input
                      onChange={(event) => setInterventionLabel(event.target.value)}
                      placeholder="Raised rear edge"
                      value={interventionLabel}
                    />
                  </label>
                  <label>
                    Intervention description
                    <textarea
                      onChange={(event) => setInterventionDescription(event.target.value)}
                      placeholder="Describe the human action taken"
                      value={interventionDescription}
                    />
                  </label>
                  <button disabled={recordingIntervention} type="submit">
                    <ClipboardCheck aria-hidden="true" />
                    {recordingIntervention ? 'Recording...' : 'Record intervention'}
                  </button>
                </form>
              )}
            </div>
          </article>

          <article className="panel collapsible-panel" id="interventions-panel" tabIndex={-1}>
            <div className="panel-head">
              <h2>Recorded interventions</h2>
              <span>{detail?.interventions.length ?? 0}</span>
            </div>
            <p className="panel-summary">{latestVerificationResult?.summary ?? detail?.interventions[0]?.description ?? 'No interventions recorded yet.'}</p>
            <div className="panel-body intervention-list">
              {detail?.interventions.length ? (
                detail.interventions.map((intervention) => (
                  <div className="intervention" key={intervention.id}>
                    <strong>{intervention.label}</strong>
                    <span>{new Date(intervention.recorded_at).toLocaleString()} / {intervention.verification_status}</span>
                    <p>{intervention.description}</p>
                    {intervention.expected_effect && <p className="counter">{intervention.expected_effect}</p>}
                    {intervention.verification_result && <VerificationResultView result={intervention.verification_result} />}
                  </div>
                ))
              ) : (
                <p className="status">No interventions recorded yet.</p>
              )}
            </div>
          </article>

          <article className="panel collapsible-panel" id="verification-panel" tabIndex={-1}>
            <div className="panel-head">
              <h2>Verification</h2>
              <span>{detail?.verification.status ?? 'Pending'}</span>
            </div>
            <p className="panel-summary">{verificationSummary}</p>
            <div className="panel-body">
              <p className="lead">{detail?.verification.summary}</p>
              <div className="signal-list">
                {detail?.verification.signals.map((signal) => <span key={signal}>{signal}</span>)}
              </div>
              {latestVerificationResult && <VerificationResultView result={latestVerificationResult} />}
            </div>
          </article>

          <article className="panel collapsible-panel" id="report-panel" tabIndex={-1}>
            <div className="panel-head">
              <h2>Report</h2>
              <span>Draft</span>
            </div>
            <p className="panel-summary">{detail?.report.summary ?? 'No report selected.'}</p>
            <div className="panel-body">
              <p className="lead">{detail?.report.summary}</p>
              <p className="next-step">{detail?.report.recommended_next_step}</p>
            </div>
          </article>
        </section>
      </section>
    </main>
  );
}
