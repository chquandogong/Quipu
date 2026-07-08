import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import {
  Activity,
  AlertTriangle,
  BatteryWarning,
  Clock3,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Cpu,
  Fan,
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

import {
  fetchFleetOverview,
  fetchInvestigationDetail,
  fetchInvestigationNotes,
  fetchInvestigationQueue,
  fetchPatternOverview,
  recordIntervention,
  recordInvestigationNote,
} from './api';
import type {
  FleetOverview,
  InvestigationDetail,
  InvestigationItem,
  InvestigationNote,
  MetricSample,
  PatternGroup,
  PatternOverview,
  RiskLevel,
  VerificationResult,
} from './types';
import './styles.css';

const flowStages = ['Detect', 'Triage', 'Investigate', 'Hypothesize', 'Act', 'Verify', 'Report'];
const appVersion = 'v0.9.0';

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
  if (metric.unit === 'boolean') return metric.value >= 0.5 ? 'Online' : 'Offline';
  if (metric.unit === 'rpm') return `${metric.value.toFixed(0)} rpm`;
  if (metric.unit === 'count') return `${metric.value.toFixed(0)}`;
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
  if (name === 'disk.root_used_percent') {
    if (value >= 95) return 'critical';
    if (value >= 85) return 'watch';
  }
  if (name === 'battery.capacity_percent') {
    if (value <= 10) return 'critical';
    if (value <= 20) return 'watch';
  }
  if (name === 'nvme.critical_warning' && value >= 1) return 'critical';
  if (name === 'nvme.available_spare_percent') {
    if (value <= 10) return 'critical';
    if (value <= 20) return 'watch';
  }
  if (name === 'nvme.percentage_used_percent') {
    if (value >= 90) return 'critical';
    if (value >= 75) return 'watch';
  }
  if (name === 'nvme.media_errors') {
    if (value >= 10) return 'critical';
    if (value > 0) return 'watch';
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

function strongestStatus(...statuses: SignalStatus[]): SignalStatus {
  if (statuses.includes('critical')) return 'critical';
  if (statuses.includes('watch')) return 'watch';
  if (statuses.includes('nominal')) return 'nominal';
  return 'missing';
}

function fanStatus(detail: InvestigationDetail | null): SignalStatus {
  const fan = latestMetric(detail, 'fan.rpm');
  if (!fan) return 'missing';
  const cpuTemp = latestMetric(detail, 'cpu.package_temp_c')?.value;
  if (fan.value <= 200 && cpuTemp !== undefined && cpuTemp >= 78) return 'watch';
  return 'nominal';
}

function nvmeHealthStatus(detail: InvestigationDetail | null): SignalStatus {
  const hasSignal = Boolean(
    latestMetric(detail, 'nvme.critical_warning')
      || latestMetric(detail, 'nvme.available_spare_percent')
      || latestMetric(detail, 'nvme.percentage_used_percent')
      || latestMetric(detail, 'nvme.media_errors'),
  );
  if (!hasSignal) return 'missing';
  return strongestStatus(
    metricStatus(detail, 'nvme.critical_warning'),
    metricStatus(detail, 'nvme.available_spare_percent'),
    metricStatus(detail, 'nvme.percentage_used_percent'),
    metricStatus(detail, 'nvme.media_errors'),
  );
}

function nvmeHealthValue(detail: InvestigationDetail | null): string {
  const criticalWarning = latestMetric(detail, 'nvme.critical_warning');
  if (criticalWarning && criticalWarning.value >= 1) return 'Critical warning';
  const availableSpare = latestMetric(detail, 'nvme.available_spare_percent');
  if (availableSpare) return `${availableSpare.value.toFixed(1)}% spare`;
  const percentageUsed = latestMetric(detail, 'nvme.percentage_used_percent');
  if (percentageUsed) return `${percentageUsed.value.toFixed(1)}% used`;
  const mediaErrors = latestMetric(detail, 'nvme.media_errors');
  if (mediaErrors) return `${mediaErrors.value.toFixed(0)} errors`;
  return 'Unavailable';
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
  const storageEvents = detail?.timeline.filter((event) => event.category === 'storage') ?? [];
  const powerEvents = detail?.timeline.filter((event) => event.category === 'power') ?? [];
  const kernelWarnings = detail?.timeline.filter(
    (event) => event.source.toLowerCase().includes('kernel') && (event.severity === 'warning' || event.severity === 'critical'),
  ) ?? [];
  const freshnessMinutes = minutesSince(overview?.generated_at, detail?.fleet_context.device.last_seen_at);
  const freshnessStatus: SignalStatus = freshnessMinutes === null ? 'missing' : freshnessMinutes > 10 ? 'critical' : freshnessMinutes > 5 ? 'watch' : 'nominal';
  const hasStorageSignal = Boolean(latestMetric(detail, 'disk.root_used_percent') || storageEvents.length);
  const hasPowerSignal = Boolean(latestMetric(detail, 'battery.capacity_percent') || latestMetric(detail, 'battery.ac_online') || powerEvents.length);
  const storageStatus = hasStorageSignal ? strongestStatus(metricStatus(detail, 'disk.root_used_percent'), storageEvents.length > 0 ? 'watch' : 'nominal') : 'missing';
  const powerStatus = hasPowerSignal ? strongestStatus(metricStatus(detail, 'battery.capacity_percent'), powerEvents.length > 0 ? 'watch' : 'nominal') : 'missing';
  const acState = metricValue(detail, 'battery.ac_online');
  const batteryValue = latestMetric(detail, 'battery.capacity_percent') ? metricValue(detail, 'battery.capacity_percent') : acState;

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
      id: 'disk.health',
      category: 'Storage',
      label: 'Disk Health',
      value: latestMetric(detail, 'disk.root_used_percent') ? metricValue(detail, 'disk.root_used_percent') : eventSignalValue(storageEvents),
      status: storageStatus,
      summary: 'root filesystem 사용률과 kernel storage warning을 함께 봅니다. (disk fullness and I/O stalls)',
      Icon: HardDrive,
    },
    {
      id: 'fan.rpm',
      category: 'Cooling',
      label: 'Fan RPM',
      value: metricValue(detail, 'fan.rpm'),
      status: fanStatus(detail),
      summary: 'hwmon에 노출된 fan 회전수를 냉각 맥락으로 봅니다. 장비별로 결측일 수 있습니다.',
      Icon: Fan,
    },
    {
      id: 'nvme.health',
      category: 'Storage',
      label: 'NVMe Health',
      value: nvmeHealthValue(detail),
      status: nvmeHealthStatus(detail),
      summary: 'critical warning, spare, lifetime usage, media error를 SMART-lite 신호로 확인합니다.',
      Icon: HardDrive,
    },
    {
      id: 'battery.power',
      category: 'Power',
      label: 'Battery Power',
      value: batteryValue,
      status: powerStatus,
      summary: `배터리 잔량, AC 상태(${acState}), power-management event를 같이 확인합니다.`,
      Icon: BatteryWarning,
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

const priorityDescriptions: Record<InvestigationItem['priority'], string> = {
  High: 'High는 즉시 확인해야 하는 항목입니다. 장애 영향이나 재발 가능성이 커서 queue 상단에 둡니다.',
  Medium: 'Medium은 지금 queue에 남겨 확인할 항목이지만 즉시 장애 수준은 아니라는 뜻입니다.',
  Low: 'Low는 관찰은 필요하지만 현재 영향이 제한적이거나 증거가 약한 항목입니다.',
};

const riskDescriptions: Record<RiskLevel, string> = {
  healthy: 'Healthy는 현재 collector evidence 기준으로 주요 warning이 보이지 않는 상태입니다.',
  warning: 'Warning은 경고 근거가 있어 확인이 필요하다는 뜻입니다. Critical은 더 높은 위험, Stale은 데이터가 오래됨입니다.',
  critical: 'Critical은 즉시 대응해야 할 위험 근거가 있는 상태입니다. 온도, 저장장치, 전원, kernel warning을 우선 확인합니다.',
  stale: 'Stale은 telemetry가 오래되어 현재 상태 판단보다 collector/agent 복구가 먼저라는 뜻입니다.',
};

const stageDescriptions: Record<string, string> = {
  Detect: 'Detect는 collector/API가 이상 신호를 발견한 단계입니다.',
  Triage: 'Triage는 감지된 근거를 분류하고 다음 조사 항목을 고르는 단계입니다.',
  Investigate: 'Investigate는 관련 metric, event, system log를 모아 원인을 좁히는 단계입니다.',
  Hypothesize: 'Hypothesize는 가능한 원인과 반대 증거, 빠진 확인 항목을 정리하는 단계입니다.',
  Act: 'Act는 냉각 조정, workload 변경, 네트워크/전원 조치 같은 개입을 기록하는 단계입니다.',
  Verify: 'Verify는 조치 전후 window를 비교해 실제로 도움이 됐는지 확인하는 단계입니다.',
  Report: 'Report는 다음 담당자나 팀이 이어받을 수 있게 결론과 근거를 남기는 단계입니다.',
};

const stageGoals: Record<string, string> = {
  Detect: '새 신호를 조사 queue로 올리는 중입니다.',
  Triage: '근거를 분류하고 조사 대상을 좁히는 중입니다.',
  Investigate: 'metric, event, log를 모아 원인을 좁히는 중입니다.',
  Hypothesize: '가능한 원인과 반대 증거를 정리하는 중입니다.',
  Act: '사람이 수행한 개입을 기록하는 중입니다.',
  Verify: '조치 전후 window를 비교하는 중입니다.',
  Report: '팀이 이어받을 결론과 근거를 남기는 중입니다.',
};

function priorityDescription(priority: InvestigationItem['priority'] | undefined): string {
  if (!priority) return '아직 조사 queue의 우선순위가 정해지지 않았습니다.';
  return priorityDescriptions[priority];
}

function riskDescription(level: RiskLevel | undefined): string {
  if (!level) return '아직 선택된 장비의 위험도 판단이 없습니다.';
  return riskDescriptions[level];
}

function stageDescription(stage: string): string {
  return stageDescriptions[stage] ?? `${stage}는 현재 조사 흐름에서 표시되는 작업 단계입니다.`;
}

function stageGoal(stage: string): string {
  return stageGoals[stage] ?? '현재 단계의 조사 목표를 좁히는 중입니다.';
}

function StatusChip({
  className,
  description,
  helpId,
  Icon,
  label,
  title,
}: {
  className?: string;
  description: string;
  helpId: string;
  Icon: typeof Activity;
  label: string;
  title: string;
}) {
  return (
    <span aria-describedby={helpId} className={['status-chip', className].filter(Boolean).join(' ')} tabIndex={0}>
      <Icon aria-hidden="true" />
      <span className="status-chip-label">{label}</span>
      <span className="status-tooltip" id={helpId} role="tooltip">
        <strong>{title}</strong>
        <span>{description}</span>
      </span>
    </span>
  );
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

function MetricRow({ detail, metric }: { detail: InvestigationDetail; metric: MetricDefinition }) {
  const status = metricStatus(detail, metric.name);
  return (
    <div className={`metric-row metric-${metric.tone} signal-${status}`}>
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

function MetricLedger({ detail }: { detail: InvestigationDetail }) {
  return (
    <dl className="metric-ledger" aria-label="Core telemetry details">
      {keyMetrics.map((metric) => (
        <MetricRow detail={detail} key={metric.name} metric={metric} />
      ))}
    </dl>
  );
}

function TelemetryBrief({ detail }: { detail: InvestigationDetail | null }) {
  if (!detail) return null;
  return (
    <section className="telemetry-brief" aria-label="Telemetry Brief">
      <span className="brief-title">Telemetry Brief</span>
      <div className="brief-readings">
      {keyMetrics.map((metric) => {
        const status = metricStatus(detail, metric.name);
        return (
          <span className={`brief-reading brief-${status}`} key={metric.name}>
            <metric.Icon aria-hidden="true" />
            <strong>{metric.shortLabel}</strong>
            <span>{metricValue(detail, metric.name)}</span>
            {status !== 'nominal' && <em>{statusLabel(status)}</em>}
          </span>
        );
      })}
      </div>
    </section>
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
          <p>Core metric 밖의 fan, NVMe health, disk, battery, Wi-Fi, memory, network, kernel, agent freshness를 한 번에 확인합니다.</p>
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

function OperationsRail({
  overview,
  patterns,
  detail,
}: {
  overview: FleetOverview | null;
  patterns: PatternOverview | null;
  detail: InvestigationDetail | null;
}) {
  const stale = overview?.summary.stale ?? 0;
  const patternCount = patterns?.category_groups.reduce((total, group) => total + group.count, 0) ?? 0;
  return (
    <section className="operations-rail" aria-label="Operations Rail">
      <article className={stale > 0 ? 'ops-card signal-watch' : 'ops-card signal-nominal'}>
        <span><Clock3 aria-hidden="true" /> Agent Freshness</span>
        <strong>{stale > 0 ? `${stale} stale` : 'Fresh'}</strong>
        <p>{detail?.fleet_context.device.last_seen_at ? `Last selected batch ${new Date(detail.fleet_context.device.last_seen_at).toLocaleString()}` : 'Waiting for selected device context.'}</p>
      </article>
      <article className="ops-card signal-nominal">
        <span><HardDrive aria-hidden="true" /> Offline Buffer</span>
        <strong>Spool-ready</strong>
        <p>Collector batches can queue locally during server or network outage.</p>
      </article>
      <article className="ops-card signal-nominal">
        <span><ShieldCheck aria-hidden="true" /> Enrollment Guard</span>
        <strong>Device-bound</strong>
        <p>Agent tokens can be created, rotated, and revoked per device.</p>
      </article>
      <article className={patternCount > 0 ? 'ops-card signal-watch' : 'ops-card signal-missing'}>
        <span><FileSearch aria-hidden="true" /> Pattern Radar</span>
        <strong>{patternCount} events</strong>
        <p>{patterns?.category_groups[0]?.category ?? 'No repeated category'} is the leading grouped signal.</p>
      </article>
    </section>
  );
}

function TeamHandoff({
  notes,
  noteBody,
  recording,
  onBodyChange,
  onSubmit,
}: {
  notes: InvestigationNote[];
  noteBody: string;
  recording: boolean;
  onBodyChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <article className="panel collapsible-panel handoff-panel" id="handoff-panel" tabIndex={-1}>
      <div className="panel-head">
        <h2>Team Handoff</h2>
        <span>{notes.length} notes</span>
      </div>
      <p className="panel-summary">{notes[notes.length - 1]?.body ?? 'No handoff note recorded yet.'}</p>
      <div className="panel-body">
        <div className="handoff-list">
          {notes.length ? (
            notes.map((note) => (
              <div className="handoff-note" key={note.id}>
                <strong>{note.author}</strong>
                <time>{new Date(note.created_at).toLocaleString()}</time>
                <p>{note.body}</p>
              </div>
            ))
          ) : (
            <p className="status">No team notes yet.</p>
          )}
        </div>
        <form className="intervention-form" onSubmit={onSubmit}>
          <label>
            Handoff note
            <textarea
              onChange={(event) => onBodyChange(event.target.value)}
              placeholder="Raised the rear edge; compare the next two batches."
              value={noteBody}
            />
          </label>
          <button disabled={recording || !noteBody.trim()} type="submit">
            <ClipboardCheck aria-hidden="true" />
            {recording ? 'Recording...' : 'Record handoff'}
          </button>
        </form>
      </div>
    </article>
  );
}

function GuidanceStrip({
  actionLabel,
  actionSummary,
  caseTitle,
  primaryEvidence,
  whyDetail,
}: {
  actionLabel: string;
  actionSummary: string;
  caseTitle: string;
  primaryEvidence: string;
  whyDetail: string;
}) {
  return (
    <section className="problem-guide" aria-label="Problem guide">
      <div className="guide-primary">
        <span>뭐가 문제지?</span>
        <strong>{caseTitle}</strong>
        <p>{primaryEvidence}</p>
      </div>
      <div>
        <span>먼저 볼 근거</span>
        <strong>{whyDetail}</strong>
      </div>
      <div>
        <span>그래서 뭘 해야 하지?</span>
        <strong>{actionLabel}</strong>
        <p>{actionSummary}</p>
      </div>
    </section>
  );
}

function workflowStageIndex(stage: string): number {
  const index = flowStages.indexOf(stage);
  return index >= 0 ? index : 0;
}

function nextWorkflowStage(stage: string): string {
  const index = workflowStageIndex(stage);
  if (index >= flowStages.length - 1) return 'Close';
  return flowStages[index + 1];
}

function WorkflowStages({ stage }: { stage: string }) {
  const currentIndex = workflowStageIndex(stage);
  return (
    <ol className="workflow-steps" aria-label="DTIHAVR stages">
      {flowStages.map((flowStage, stageIndex) => {
        const isActive = flowStage === stage;
        const isComplete = stageIndex < currentIndex;
        return (
          <li
            aria-current={isActive ? 'step' : undefined}
            className={[
              'workflow-step',
              isActive ? 'active' : '',
              isComplete ? 'complete' : '',
            ].filter(Boolean).join(' ')}
            key={flowStage}
            tabIndex={0}
          >
            <span aria-hidden="true">{flowStage[0]}</span>
            <span className="workflow-step-tooltip" role="tooltip">
              <strong>{flowStage}</strong>
              <span>{stageDescription(flowStage)}</span>
            </span>
          </li>
        );
      })}
    </ol>
  );
}

function WorkflowRail({
  actionLabel,
  proofSummary,
  stage,
}: {
  actionLabel: string;
  proofSummary: string;
  stage: string;
}) {
  const index = workflowStageIndex(stage);
  const progress = Math.round((index / (flowStages.length - 1)) * 100);
  const nextStage = nextWorkflowStage(stage);
  return (
    <section className="workflow-rail" aria-label="Workflow rail">
      <div className="workflow-copy">
        <span>DTIHAVR</span>
        <strong>{stage} -&gt; {nextStage}</strong>
        <p>{stageGoal(stage)}</p>
      </div>
      <div className="workflow-progress">
        <div className="workflow-track" aria-label={`Workflow progress ${progress}%`}>
          <span style={{ width: `${progress}%` }} />
        </div>
        <WorkflowStages stage={stage} />
      </div>
      <div className="workflow-next">
        <span>Next</span>
        <strong>{actionLabel}</strong>
        <p>{proofSummary}</p>
      </div>
    </section>
  );
}

function FleetBrief({ overview, queueLength }: { overview: FleetOverview | null; queueLength: number }) {
  const summary = overview?.summary;
  const stats = [
    { label: 'Total', value: summary?.total ?? 0, tone: 'neutral' },
    { label: 'Critical', value: summary?.critical ?? 0, tone: 'critical' },
    { label: 'Warning', value: summary?.warning ?? 0, tone: 'warning' },
    { label: 'Queue', value: queueLength, tone: 'queue' },
  ];

  return (
    <section className="fleet-brief" aria-label="Fleet Brief">
      <span className="brief-title">Fleet Brief</span>
      <div className="fleet-readings">
        {stats.map((stat) => (
          <span className={`fleet-reading fleet-${stat.tone}`} key={stat.label}>
            <strong>{stat.value}</strong>
            <span>{stat.label}</span>
          </span>
        ))}
      </div>
    </section>
  );
}

function groupTitle(group: PatternGroup, keyName: 'category' | 'model' | 'kernel_version' | 'component'): string {
  return group[keyName] ?? 'Unknown';
}

function PatternGroupList({
  title,
  groups,
  keyName,
}: {
  title: string;
  groups: PatternGroup[];
  keyName: 'category' | 'model' | 'kernel_version' | 'component';
}) {
  return (
    <div className="pattern-column">
      <h3>{title}</h3>
      {groups.slice(0, 4).map((group) => (
        <div className="pattern-row" key={`${title}-${groupTitle(group, keyName)}`}>
          <strong>{groupTitle(group, keyName)}</strong>
          <span>{group.count} events / {group.device_count} devices</span>
          <em>{group.severities.critical} critical · {group.severities.warning} warning</em>
        </div>
      ))}
      {groups.length === 0 && <p className="status">No patterns yet.</p>}
    </div>
  );
}

function PatternExplorer({ patterns }: { patterns: PatternOverview | null }) {
  const componentGroups = patterns?.component_groups ?? [];
  return (
    <article className="panel collapsible-panel pattern-panel" id="pattern-panel" tabIndex={-1}>
      <div className="panel-head">
        <h2>Pattern Explorer</h2>
        <span>{(patterns?.category_groups.length ?? 0) + componentGroups.length} groups</span>
      </div>
      <p className="panel-summary">
        {componentGroups[0]
          ? `${componentGroups[0].component} is the leading component signature.`
          : patterns?.category_groups[0]
            ? `${patterns.category_groups[0].category} leads with ${patterns.category_groups[0].count} grouped event(s).`
          : 'No grouped pattern yet.'}
      </p>
      <div className="panel-body pattern-grid">
        <PatternGroupList title="By category" groups={patterns?.category_groups ?? []} keyName="category" />
        <PatternGroupList title="By component" groups={componentGroups} keyName="component" />
        <PatternGroupList title="By model" groups={patterns?.model_groups ?? []} keyName="model" />
        <PatternGroupList title="By kernel" groups={patterns?.kernel_groups ?? []} keyName="kernel_version" />
      </div>
    </article>
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
  const [patterns, setPatterns] = useState<PatternOverview | null>(null);
  const [notes, setNotes] = useState<InvestigationNote[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [interventionLabel, setInterventionLabel] = useState('');
  const [interventionDescription, setInterventionDescription] = useState('');
  const [noteBody, setNoteBody] = useState('');
  const [recordingIntervention, setRecordingIntervention] = useState(false);
  const [recordingNote, setRecordingNote] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    Promise.all([fetchFleetOverview(), fetchInvestigationQueue(), fetchPatternOverview()])
      .then(([fleetData, queueData, patternData]) => {
        if (!active) return;
        setOverview(fleetData);
        setQueue(queueData.items);
        setPatterns(patternData);
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
    Promise.all([fetchInvestigationDetail(selectedId), fetchInvestigationNotes(selectedId)])
      .then(([detailData, notesData]) => {
        if (!active) return;
        setDetail(detailData);
        setNotes(notesData.notes);
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
  const selectedRiskLevel = detail?.item.risk_level ?? selectedItem?.risk_level;
  const deviceLabel = detail?.fleet_context.device.hostname ?? selectedItem?.device_hostname ?? 'No device selected';
  const caseTitle = detail?.item.title ?? selectedItem?.title ?? 'Select an investigation';
  const riskLabel = selectedRiskLevel ? riskLabels[selectedRiskLevel] : 'No risk';
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

  async function handleRecordNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedId || !noteBody.trim()) return;
    setRecordingNote(true);
    try {
      const created = await recordInvestigationNote(selectedId, {
        author: 'ops',
        body: noteBody,
        created_at: new Date().toISOString(),
      });
      setNotes([...notes, created]);
      setNoteBody('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unknown handoff API error');
    } finally {
      setRecordingNote(false);
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
            <StatusChip
              className={selectedItem ? priorityClass(selectedItem.priority) : 'status-neutral'}
              description={priorityDescription(selectedItem?.priority)}
              helpId="selected-priority-help"
              Icon={AlertTriangle}
              label={selectedItem?.priority ?? 'No priority'}
              title="Priority / 우선순위"
            />
            <StatusChip
              className={selectedRiskLevel ? riskClass(selectedRiskLevel) : 'status-neutral'}
              description={riskDescription(selectedRiskLevel)}
              helpId="selected-risk-help"
              Icon={ShieldCheck}
              label={riskLabel}
              title="Risk level / 위험도"
            />
            <StatusChip
              className="status-stage"
              description={stageDescription(selectedStage)}
              helpId="selected-stage-help"
              Icon={ListChecks}
              label={selectedStage}
              title="Workflow stage / 진행 단계"
            />
          </div>
        </div>

        <GuidanceStrip
          actionLabel={actionLabel}
          actionSummary={actionSummary}
          caseTitle={caseTitle}
          primaryEvidence={primaryEvidence}
          whyDetail={whyDetail}
        />

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

        <TelemetryBrief detail={detail} />

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
          <FleetBrief overview={overview} queueLength={queue.length} />
          <WorkflowRail actionLabel={actionLabel} proofSummary={proofSummary} stage={selectedStage} />
        </div>
      </section>

      <OperationsRail overview={overview} patterns={patterns} detail={detail} />

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
            {detail && <MetricLedger detail={detail} />}
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

          <TeamHandoff
            notes={notes}
            noteBody={noteBody}
            recording={recordingNote}
            onBodyChange={setNoteBody}
            onSubmit={handleRecordNote}
          />

          <PatternExplorer patterns={patterns} />

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
