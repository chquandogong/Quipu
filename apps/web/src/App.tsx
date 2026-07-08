import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import {
  Activity,
  AlertTriangle,
  Clock3,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Cpu,
  FileSearch,
  Gauge,
  HardDrive,
  HelpCircle,
  Info,
  ListChecks,
  MemoryStick,
  MousePointer2,
  Network,
  ServerCrash,
  ShieldCheck,
  Tag,
  Thermometer,
  UserRound,
  Wifi,
} from 'lucide-react';

import { fetchFleetOverview, fetchInvestigationDetail, fetchInvestigationQueue, recordIntervention } from './api';
import type { FleetOverview, InvestigationDetail, InvestigationItem, MetricSample, RiskLevel, VerificationResult } from './types';
import './styles.css';

const flowStages = ['Detect', 'Triage', 'Investigate', 'Hypothesize', 'Act', 'Verify', 'Report'];
const appVersion = 'v0.4.0';

const riskLabels: Record<RiskLevel, string> = {
  healthy: 'Healthy',
  warning: 'Warning',
  critical: 'Critical',
  stale: 'Stale',
};

type SignalStatus = 'nominal' | 'watch' | 'critical' | 'missing';

type MetricDefinition = {
  name: string;
  label: string;
  shortLabel: string;
  ariaLabel: string;
  Icon: typeof Activity;
  definition: string;
  window: string;
  reading: string;
  nextCheck: string;
  tone: 'thermal' | 'compute' | 'storage' | 'network';
};

const keyMetrics: MetricDefinition[] = [
  {
    name: 'cpu.package_temp_c',
    label: 'CPU Package',
    shortLabel: 'CPU',
    ariaLabel: 'CPU package temperature',
    Icon: Thermometer,
    definition: '선택한 장비의 CPU 패키지 센서 온도입니다. (CPU package temperature)',
    window: '가장 최근 collector 샘플입니다. 가까운 샘플과 비교해야 추세를 판단할 수 있습니다.',
    reading: '지속적인 80도 중반 이상은 대부분의 노트북에서 thermal warning으로 봅니다.',
    nextCheck: '팬 흡기, 바닥 clearance, workload, 새 kernel thermal warning을 함께 확인합니다.',
    tone: 'thermal',
  },
  {
    name: 'cpu.load_1m',
    label: 'Load Average',
    shortLabel: 'Load',
    ariaLabel: '1 minute load average',
    Icon: Cpu,
    definition: '최근 1분 동안 실행 중이거나 대기 중인 작업 평균입니다. (1-minute load average)',
    window: 'Linux 1분 load average이며, 순간 CPU percent가 아닙니다.',
    reading: 'CPU 코어 수와 온도 추세를 함께 봐야 과부하인지 판단할 수 있습니다.',
    nextCheck: 'load와 온도가 같이 오르면 실행 중인 작업과 냉각 조건을 같이 봅니다.',
    tone: 'compute',
  },
  {
    name: 'nvme.temp_c',
    label: 'NVMe SSD',
    shortLabel: 'NVMe',
    ariaLabel: 'NVMe SSD temperature',
    Icon: HardDrive,
    definition: '선택한 장비의 저장장치 온도입니다. (NVMe SSD temperature)',
    window: 'storage telemetry에서 들어온 가장 최근 collector 샘플입니다.',
    reading: '40도 초반은 보통 정상 범위이며, 지속적인 고온은 신뢰성 문제로 이어질 수 있습니다.',
    nextCheck: 'I/O workload, chassis heat, SMART warning, kernel storage warning을 같이 확인합니다.',
    tone: 'storage',
  },
  {
    name: 'wifi.signal_dbm',
    label: 'Wi-Fi Signal',
    shortLabel: 'Wi-Fi',
    ariaLabel: 'Wi-Fi signal strength',
    Icon: Wifi,
    definition: '무선 연결의 수신 신호 강도입니다. (Wi-Fi signal strength, dBm)',
    window: '/proc/net/wireless에서 읽은 가장 최근 collector 샘플입니다.',
    reading: '0에 가까울수록 강합니다. -70 dBm 이하는 불안정 가능성이 커집니다.',
    nextCheck: 'signal drop, reconnect event, NetworkManager 로그, AP 거리나 간섭을 함께 확인합니다.',
    tone: 'network',
  },
];

type TelemetryTile = {
  id: string;
  category: string;
  label: string;
  value: string;
  status: SignalStatus;
  summary: string;
  Icon: typeof Activity;
};

function latestMetric(detail: InvestigationDetail | null, name: string): MetricSample | undefined {
  return detail?.fleet_context.latest_metrics[name];
}

function metricValue(detail: InvestigationDetail | null, name: string): string {
  const metric = latestMetric(detail, name);
  if (!metric) return 'Unavailable';
  if (metric.unit === 'celsius') return `${metric.value.toFixed(1)}C`;
  if (metric.unit === 'percent') return `${metric.value.toFixed(1)}%`;
  if (metric.unit === 'dbm') return `${metric.value.toFixed(0)} dBm`;
  return `${metric.value}`;
}

function observedTime(detail: InvestigationDetail | null, name: string): string {
  const observedAt = latestMetric(detail, name)?.observed_at;
  if (!observedAt) return 'No sample time';
  return new Date(observedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function metricStatus(detail: InvestigationDetail | null, name: string): SignalStatus {
  const metric = latestMetric(detail, name);
  if (!metric) return 'missing';
  const value = metric.value;
  if (name === 'cpu.package_temp_c') {
    if (value >= 90) return 'critical';
    if (value >= 78) return 'watch';
  }
  if (name === 'cpu.load_1m' && value >= 4) return 'watch';
  if (name === 'nvme.temp_c') {
    if (value >= 75) return 'critical';
    if (value >= 60) return 'watch';
  }
  if (name === 'memory.used_percent') {
    if (value >= 95) return 'critical';
    if (value >= 85) return 'watch';
  }
  if (name === 'wifi.signal_dbm') {
    if (value <= -80) return 'critical';
    if (value <= -70) return 'watch';
  }
  return 'nominal';
}

function statusLabel(status: SignalStatus): string {
  return {
    nominal: 'Nominal',
    watch: 'Watch',
    critical: 'Critical',
    missing: 'No data',
  }[status];
}

function warningCountText(count: number): string {
  if (count === 1) return '1 warning';
  return `${count} warnings`;
}

function eventSignalValue(events: InvestigationDetail['timeline']): string {
  const warningCount = events.filter((event) => event.severity === 'warning' || event.severity === 'critical').length;
  if (warningCount > 0) return warningCountText(warningCount);
  if (events.length === 1) return '1 event';
  return `${events.length} events`;
}

function eventMatches(event: InvestigationDetail['timeline'][number], patterns: string[]): boolean {
  const text = `${event.summary} ${event.source} ${event.category}`.toLowerCase();
  return patterns.some((pattern) => text.includes(pattern));
}

function minutesSince(laterIso: string | undefined, earlierIso: string | undefined): number | null {
  if (!laterIso || !earlierIso) return null;
  const later = new Date(laterIso).getTime();
  const earlier = new Date(earlierIso).getTime();
  if (Number.isNaN(later) || Number.isNaN(earlier)) return null;
  return Math.max(0, Math.round((later - earlier) / 60000));
}

function buildTelemetryTiles(detail: InvestigationDetail | null, overview: FleetOverview | null): TelemetryTile[] {
  const networkEvents = detail?.timeline.filter((event) => event.category === 'network') ?? [];
  const reconnectEvents = networkEvents.filter((event) => eventMatches(event, ['disconnect', 'reconnect', 'carrier', 'supplicant', 'dhcp', 'state change']));
  const throttlingEvents = detail?.timeline.filter((event) => event.category === 'thermal' && eventMatches(event, ['throttl', 'above threshold', 'critical temperature'])) ?? [];
  const kernelWarnings = detail?.timeline.filter(
    (event) => event.source.toLowerCase().includes('kernel') && (event.severity === 'warning' || event.severity === 'critical'),
  ) ?? [];
  const freshnessMinutes = minutesSince(overview?.generated_at, detail?.fleet_context.device.last_seen_at);
  const freshnessStatus: SignalStatus = freshnessMinutes === null ? 'missing' : freshnessMinutes > 10 ? 'critical' : freshnessMinutes > 5 ? 'watch' : 'nominal';

  return [
    {
      id: 'memory.used_percent',
      category: 'Compute',
      label: 'Memory Used',
      value: metricValue(detail, 'memory.used_percent'),
      status: metricStatus(detail, 'memory.used_percent'),
      summary: '프로세스 압박이나 swap 가능성을 판단하는 보조 신호입니다. (memory pressure)',
      Icon: MemoryStick,
    },
    {
      id: 'network.events',
      category: 'Network',
      label: 'Network Events',
      value: eventSignalValue(networkEvents),
      status: networkEvents.length > 0 ? 'watch' : 'nominal',
      summary: 'reconnect, carrier loss, NetworkManager warning이 조사 흐름에 포함됐는지 봅니다.',
      Icon: Network,
    },
    {
      id: 'network.reconnects',
      category: 'Network',
      label: 'Reconnect History',
      value: eventSignalValue(reconnectEvents),
      status: reconnectEvents.length > 0 ? 'watch' : 'nominal',
      summary: 'Wi-Fi disconnect/reconnect 흐름이 반복되는지 직접 확인합니다. (reconnect history)',
      Icon: Wifi,
    },
    {
      id: 'thermal.throttling',
      category: 'Thermal',
      label: 'Thermal Throttling',
      value: eventSignalValue(throttlingEvents),
      status: throttlingEvents.length > 0 ? 'watch' : 'nominal',
      summary: 'kernel thermal throttling이나 threshold event가 실제로 발생했는지 봅니다.',
      Icon: Thermometer,
    },
    {
      id: 'kernel.warnings',
      category: 'Reliability',
      label: 'Kernel Warnings',
      value: eventSignalValue(kernelWarnings),
      status: kernelWarnings.length > 0 ? 'watch' : 'nominal',
      summary: 'thermal, storage, graphics 같은 kernel warning이 재발했는지 확인합니다.',
      Icon: ServerCrash,
    },
    {
      id: 'agent.freshness',
      category: 'Telemetry',
      label: 'Agent Freshness',
      value: freshnessMinutes === null ? 'Unavailable' : freshnessMinutes <= 0 ? 'just now' : `${freshnessMinutes} min ago`,
      status: freshnessStatus,
      summary: '데이터가 오래되면 현재 상태 판단보다 collector/agent 복구가 먼저입니다.',
      Icon: Clock3,
    },
  ];
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

function MetricCard({ detail, metric }: { detail: InvestigationDetail; metric: MetricDefinition }) {
  const status = metricStatus(detail, metric.name);
  return (
    <div className={`metric-card metric-${metric.tone} signal-${status}`}>
      <div className="metric-topline">
        <dt className="metric-name">
          <metric.Icon aria-hidden="true" />
          {metric.label}
        </dt>
        <div className="metric-help">
          <button aria-describedby={`${metric.name}-help`} aria-label={`Explain ${metric.ariaLabel} metric`} type="button">
            <HelpCircle aria-hidden="true" />
          </button>
          <div className="metric-tooltip" id={`${metric.name}-help`} role="tooltip">
            <strong>{metric.ariaLabel}</strong>
            <span>정의: {metric.definition}</span>
            <span>시간창: {metric.window}</span>
            <span>해석: {metric.reading}</span>
            <span>다음 확인: {metric.nextCheck}</span>
          </div>
        </div>
      </div>
      <dd>{metricValue(detail, metric.name)}</dd>
      <span className="metric-observed">{metric.shortLabel} / {statusLabel(status)} / observed {observedTime(detail, metric.name)}</span>
    </div>
  );
}

function SignalConsole({ detail }: { detail: InvestigationDetail | null }) {
  if (!detail) return null;
  return (
    <div className="signal-console" aria-label="First glance telemetry signals">
      {keyMetrics.map((metric) => {
        const status = metricStatus(detail, metric.name);
        return (
          <div className={`signal-chip signal-${status}`} key={metric.name}>
            <span>
              <metric.Icon aria-hidden="true" />
              {metric.shortLabel}
            </span>
            <strong>{metricValue(detail, metric.name)}</strong>
            <em>{statusLabel(status)}</em>
          </div>
        );
      })}
    </div>
  );
}

function TelemetryMatrix({ detail, overview }: { detail: InvestigationDetail | null; overview: FleetOverview | null }) {
  if (!detail) return null;
  const tiles = buildTelemetryTiles(detail, overview);
  return (
    <section className="telemetry-matrix" aria-label="Telemetry coverage matrix">
      <div className="matrix-head">
        <div>
          <h3>Telemetry Matrix</h3>
          <p>Core metric 밖의 Wi-Fi, memory, network, kernel, agent freshness를 한 번에 확인합니다.</p>
        </div>
        <span>{tiles.filter((tile) => tile.status !== 'missing').length}/{tiles.length} signals</span>
      </div>
      <div className="telemetry-grid">
        {tiles.map((tile) => (
          <article className={`telemetry-tile signal-${tile.status}`} key={tile.id}>
            <span className="telemetry-category">{tile.category}</span>
            <div className="telemetry-value">
              <tile.Icon aria-hidden="true" />
              <strong>{tile.value}</strong>
            </div>
            <h4>{tile.label}</h4>
            <p>{tile.summary}</p>
          </article>
        ))}
      </div>
    </section>
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
  const primaryEvidence = detail?.item.evidence ?? detail?.timeline[0]?.summary ?? 'Select a queue item to inspect evidence.';
  const verificationLabel = detail?.verification.status ?? 'Pending';
  const verificationSummary = detail?.verification.summary ?? 'Record an intervention before verification.';
  const selectedStage = selectedItem?.stage ?? 'Detect';
  const deviceLabel = detail?.fleet_context.device.hostname ?? selectedItem?.device_hostname ?? 'No device selected';
  const caseTitle = detail?.item.title ?? selectedItem?.title ?? 'Select an investigation';
  const riskLabel = detail ? riskLabels[detail.item.risk_level] : 'No risk';
  const whyNow = detail?.item.evidence ?? selectedItem?.why_now ?? 'Choose a queue item to see the evidence.';
  const whyDetail = detail?.item.category === 'agent'
    ? 'Fresh telemetry is required before trusting older thermal, load, or storage readings.'
    : detail?.hypotheses[0]?.contradicting_evidence[0]
      ?? detail?.hypotheses[0]?.supporting_evidence[0]
      ?? 'Evidence appears after selecting an investigation.';
  const actionLabel = nextAction?.label ?? selectedItem?.next_step ?? 'Select a queue item';
  const actionSummary = nextAction?.description ?? selectedItem?.next_step ?? 'Choose an investigation before recording action.';
  const proofSummary = latestVerificationResult?.summary ?? verificationSummary;

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
    <main className="page page-command-dark">
      <header className="topbar">
        <div>
          <p className="eyebrow">Team workstation health investigator</p>
          <h1>Quipu</h1>
        </div>
        <div className="topbar-meta">
          <p className="generated">Detect - triage - verify with evidence</p>
          <div className="meta-chips" aria-label="Project metadata">
            <a className="meta-chip" href="https://github.com/chquandogong/CHENGHAO-QUAN" target="_blank" rel="noreferrer">
              <UserRound aria-hidden="true" />
              Made by Dr. 권성호
            </a>
            <span className="meta-chip">
              <Info aria-hidden="true" />
              About: workstation health investigation
            </span>
            <span className="meta-chip">
              <Tag aria-hidden="true" />
              Version {appVersion}
            </span>
          </div>
        </div>
      </header>

      <section className="command-center" aria-label="Investigation command center">
        <div className="command-head">
          <div>
            <p className="command-kicker">Command Center</p>
            <h2>{deviceLabel}</h2>
            <p>{caseTitle}</p>
          </div>
          <div className="case-badges" aria-label="Selected case status">
            <span><AlertTriangle aria-hidden="true" /> {selectedItem?.priority ?? 'No priority'}</span>
            <span><ShieldCheck aria-hidden="true" /> {riskLabel}</span>
            <span><ListChecks aria-hidden="true" /> {selectedStage}</span>
          </div>
        </div>

        <div className="answer-grid">
          <article className="answer-card answer-primary">
            <span className="answer-label"><FileSearch aria-hidden="true" /> Inspect now <small>지금 확인</small></span>
            <strong>{caseTitle}</strong>
            <p>{primaryEvidence}</p>
          </article>
          <article className="answer-card">
            <span className="answer-label"><AlertTriangle aria-hidden="true" /> Why it matters <small>판단 근거</small></span>
            <strong>{whyNow}</strong>
            <p>{whyDetail}</p>
          </article>
          <article className="answer-card">
            <span className="answer-label"><ChevronRight aria-hidden="true" /> Do next <small>다음 행동</small></span>
            <strong>{actionLabel}</strong>
            <p>{actionSummary}</p>
          </article>
          <article className="answer-card">
            <span className="answer-label"><CheckCircle2 aria-hidden="true" /> Proof needed <small>검증 조건</small></span>
            <strong>{verificationLabel}</strong>
            <p>{proofSummary}</p>
          </article>
        </div>

        <SignalConsole detail={detail} />

        <div className="command-actions" aria-label="Primary investigation actions">
          <button onClick={() => scrollToPanel('evidence-panel')} type="button">
            <MousePointer2 aria-hidden="true" />
            Review evidence
          </button>
          <button onClick={() => scrollToPanel('action-plan')} type="button">
            <ClipboardCheck aria-hidden="true" />
            Record action
          </button>
          <button onClick={() => scrollToPanel('verification-panel')} type="button">
            <Gauge aria-hidden="true" />
            Verify result
          </button>
        </div>

        <div className="command-footer">
          <div className="health-strip" aria-label="Fleet health strip">
            <span><strong>{overview?.summary.total ?? 0}</strong>Total</span>
            <span><strong>{overview?.summary.critical ?? 0}</strong>Critical</span>
            <span><strong>{overview?.summary.warning ?? 0}</strong>Warning</span>
            <span><strong>{queue.length}</strong>Queue</span>
          </div>
          <div className="stage-strip" aria-label="DTIHAVR workflow">
            {flowStages.map((stage) => (
              <span
                aria-current={selectedStage === stage ? 'step' : undefined}
                className={selectedStage === stage ? 'active' : undefined}
                key={stage}
              >
                {stage}
              </span>
            ))}
          </div>
        </div>
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
                {keyMetrics.map((metric) => (
                  <MetricCard detail={detail} key={metric.name} metric={metric} />
                ))}
              </dl>
            )}
            <TelemetryMatrix detail={detail} overview={overview} />
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
