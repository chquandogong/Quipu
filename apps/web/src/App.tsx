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
  DeviceSnapshot,
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
const appVersion = 'v0.14.2';

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

const baseKeyMetrics: MetricDefinition[] = [
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
    ariaLabel: 'Linux load average windows',
    Icon: Cpu,
    definition: '최근 1/5/15분 동안 실행 중이거나 대기 중인 작업 평균입니다. (Linux load average)',
    window: 'Linux 표준 load average window입니다. 10분 값은 기본 제공되지 않으므로 임의 계산하지 않습니다.',
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

function windowsThermalMetric(metricName: string): MetricDefinition {
  return {
    name: metricName,
    label: 'Windows Thermal',
    shortLabel: 'Thermal',
    ariaLabel: 'Windows thermal zone temperature',
    Icon: Thermometer,
    definition: 'Windows가 노출한 ACPI thermal zone 온도입니다. CPU package/core 센서와 같은 항목으로 강제 변환하지 않습니다.',
    window: '가장 최근 Windows collector 샘플입니다.',
    reading: '장비/펌웨어가 제공하는 zone 값입니다. CPU core 온도와 직접 1:1로 비교하지 않습니다.',
    nextCheck: '같은 장비의 NVMe 온도, 전원 이벤트, 팬 노출 여부를 함께 봅니다.',
    tone: 'thermal',
  };
}

function windowsCpuTemperatureMetric(): MetricDefinition {
  return {
    name: 'cpu.package_temp_c',
    label: 'CPU Cores',
    shortLabel: 'CPU',
    ariaLabel: 'Windows CPU core temperatures',
    Icon: Thermometer,
    definition: 'LibreHardwareMonitor/OpenHardwareMonitor가 노출한 Windows CPU P-core/E-core/core 온도입니다.',
    window: '가장 최근 Windows collector 샘플입니다.',
    reading: 'P-core/E-core별 값을 그대로 보여줍니다. CPU package 센서가 없으면 core 중 최고 온도를 대표값으로 봅니다.',
    nextCheck: 'core별 load, thermal zone, NVMe 온도, 팬 RPM 노출 여부를 함께 확인합니다.',
    tone: 'thermal',
  };
}

const windowsCpuLoadMetric: MetricDefinition = {
  name: 'cpu.load_percent',
  label: 'CPU Core Load',
  shortLabel: 'Load',
  ariaLabel: 'Windows CPU core load',
  Icon: Cpu,
  definition: 'LibreHardwareMonitor/OpenHardwareMonitor가 노출한 CPU total/core별 사용률입니다. Linux load average와 다른 percent 값입니다.',
  window: '가장 최근 Windows collector 샘플입니다.',
  reading: '값은 percent입니다. 특정 P-core/E-core만 높으면 단일 thread workload 가능성이 큽니다.',
  nextCheck: '높은 core load와 같은 시각의 core 온도를 같이 봅니다.',
  tone: 'compute',
};

type TelemetryTile = {
  id: string;
  category: string;
  label: string;
  value: string;
  status: SignalStatus;
  summary: string;
  Icon: typeof Activity;
};

type CoreTemperature = {
  index: string;
  key: string;
  sample: MetricSample;
  status: SignalStatus;
  group?: string;
};

type CoreLoad = {
  index: string;
  key: string;
  sample: MetricSample;
  status: SignalStatus;
  group?: string;
};

type MetricBreakdownItem = {
  key: string;
  label: string;
  value: string;
  status: SignalStatus;
  ariaLabel: string;
  group?: string;
};

type MetricBreakdown = {
  title: string;
  items: MetricBreakdownItem[];
  emptyLabel?: string;
  emptyAriaLabel?: string;
};

function latestMetric(detail: InvestigationDetail | null, name: string): MetricSample | undefined {
  return detail?.fleet_context.latest_metrics[name];
}

function metricSampleValue(metric: MetricSample | undefined): string {
  if (!metric) return 'Unavailable';
  if (metric.unit === 'celsius') return `${metric.value.toFixed(1)}C`;
  if (metric.unit === 'percent') return `${metric.value.toFixed(1)}%`;
  if (metric.unit === 'dbm') return `${metric.value.toFixed(0)} dBm`;
  if (metric.unit === 'load') return metric.value.toFixed(2);
  if (metric.unit === 'boolean') return metric.value >= 0.5 ? 'Online' : 'Offline';
  if (metric.unit === 'rpm') return `${metric.value.toFixed(0)} rpm`;
  if (metric.unit === 'count') return `${metric.value.toFixed(0)}`;
  if (metric.unit === 'bytes') return formatBytes(metric.value);
  if (metric.unit === 'bytes_per_sec') return `${formatBytes(metric.value)}/s`;
  if (metric.unit === 'mbps') return `${metric.value.toFixed(metric.value >= 100 ? 0 : 1)} Mbps`;
  return `${metric.value}`;
}

function breakdownSampleValue(metric: MetricSample | undefined): string {
  return metric ? metricSampleValue(metric) : '-';
}

function cpuTemperatureSamples(detail: InvestigationDetail | null): MetricSample[] {
  if (!detail) return [];
  const packageSample = latestMetric(detail, 'cpu.package_temp_c');
  const coreSamples = cpuCoreBreakdown(detail).map((core) => core.sample);
  return packageSample ? [packageSample, ...coreSamples] : coreSamples;
}

function cpuTemperatureValue(detail: InvestigationDetail | null): string {
  const packageSample = latestMetric(detail, 'cpu.package_temp_c');
  if (packageSample) return metricSampleValue(packageSample);
  const samples = cpuTemperatureSamples(detail);
  if (samples.length === 0) return 'Unavailable';
  return `Max ${metricSampleValue(samples.reduce((max, sample) => (sample.value > max.value ? sample : max), samples[0]))}`;
}

function metricValue(detail: InvestigationDetail | null, name: string): string {
  if (name === 'cpu.package_temp_c') return cpuTemperatureValue(detail);
  return metricSampleValue(latestMetric(detail, name));
}

function observedTime(detail: InvestigationDetail | null, name: string): string {
  const observedAt = latestMetric(detail, name)?.observed_at
    ?? (name === 'cpu.package_temp_c' ? cpuTemperatureSamples(detail)[0]?.observed_at : undefined);
  if (!observedAt) return 'No sample time';
  return new Date(observedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function compareLabel(left: string, right: string): number {
  return left.localeCompare(right, undefined, { numeric: true, sensitivity: 'base' });
}

function formatBytes(value: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  let scaled = Math.max(0, value);
  let unitIndex = 0;
  while (scaled >= 1024 && unitIndex < units.length - 1) {
    scaled /= 1024;
    unitIndex += 1;
  }
  const precision = Number.isInteger(scaled) || scaled >= 100 || unitIndex === 0 ? 0 : scaled >= 10 ? 1 : 2;
  return `${scaled.toFixed(precision)} ${units[unitIndex]}`;
}

function compactCpuModel(model: string | null | undefined): string {
  if (!model) return 'Unknown CPU';
  return model
    .replace(/\(R\)/g, '')
    .replace(/\(TM\)/g, '')
    .replace(/\s+CPU\s+/i, ' ')
    .replace(/\s+@.+$/, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function coreTemperatureStatus(sample: MetricSample): SignalStatus {
  if (sample.value >= 90) return 'critical';
  if (sample.value >= 78) return 'watch';
  return 'nominal';
}

function coreLoadStatus(sample: MetricSample): SignalStatus {
  if (sample.value >= 95) return 'critical';
  if (sample.value >= 85) return 'watch';
  return 'nominal';
}

function parseCpuCoreMetric(metricName: string, suffix: 'temp_c' | 'load_percent'): { index: string; group?: string } | null {
  const match = metricName.match(new RegExp(`^cpu\\.(?:(p|e|lp_e)_)?core_(\\d+)\\.${suffix}$`));
  if (!match) return null;
  const group = match[1] === 'p' ? 'P' : match[1] === 'e' ? 'E' : match[1] === 'lp_e' ? 'LP-E' : undefined;
  return { index: match[2], group };
}

function cpuCoreBreakdown(detail: InvestigationDetail): CoreTemperature[] {
  return Object.entries(detail.fleet_context.latest_metrics)
    .map(([metricName, sample]) => {
      const parsed = parseCpuCoreMetric(metricName, 'temp_c');
      return parsed ? { ...parsed, key: metricName, sample, status: coreTemperatureStatus(sample) } : null;
    })
    .filter((core): core is CoreTemperature => core !== null)
    .sort((left, right) => compareLabel(`${left.group ?? 'Z'}-${left.index}`, `${right.group ?? 'Z'}-${right.index}`));
}

function cpuLoadBreakdown(detail: InvestigationDetail): CoreLoad[] {
  return Object.entries(detail.fleet_context.latest_metrics)
    .map(([metricName, sample]) => {
      const parsed = parseCpuCoreMetric(metricName, 'load_percent');
      return parsed ? { ...parsed, key: metricName, sample, status: coreLoadStatus(sample) } : null;
    })
    .filter((core): core is CoreLoad => core !== null)
    .sort((left, right) => compareLabel(`${left.group ?? 'Z'}-${left.index}`, `${right.group ?? 'Z'}-${right.index}`));
}

function coreTypeGroupsForUltra5_125H(cores: CoreTemperature[]): Map<string, string> {
  const coreIds = cores.map((core) => Number(core.index)).filter(Number.isInteger);
  const expectedIds = [0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 20, 32, 33];
  if (
    coreIds.length !== expectedIds.length
    || expectedIds.some((expectedId) => !coreIds.includes(expectedId))
  ) {
    return new Map();
  }
  return new Map([
    ...[8, 12, 16, 20].map((coreId): [string, string] => [String(coreId), 'P']),
    ...[0, 1, 2, 3, 4, 5, 6, 7].map((coreId): [string, string] => [String(coreId), 'E']),
    ...[32, 33].map((coreId): [string, string] => [String(coreId), 'LP-E']),
  ]);
}

function statusForMetricSample(name: string, sample: MetricSample | undefined): SignalStatus {
  if (!sample) return 'missing';
  const value = sample.value;
  if (name === 'cpu.package_temp_c' || /^cpu\.core_\d+\.temp_c$/.test(name)) {
    if (value >= 90) return 'critical';
    if (value >= 78) return 'watch';
  }
  if (/^cpu\.load_(1m|5m|15m)$/.test(name) && value >= 4) return 'watch';
  if (name === 'cpu.load_percent' || /^cpu\.(?:(?:p|e|lp_e)_)?core_\d+\.load_percent$/.test(name)) {
    if (value >= 95) return 'critical';
    if (value >= 85) return 'watch';
  }
  if (name === 'nvme.temp_c' || /^nvme\.[^.]+\.temp_c$/.test(name)) {
    if (value >= 75) return 'critical';
    if (value >= 60) return 'watch';
  }
  if (/^thermal\..*\.temp_c$/.test(name)) {
    if (value >= 90) return 'critical';
    if (value >= 78) return 'watch';
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
  if ((name === 'nvme.smart_passed' || /^nvme\.[^.]+\.smart_passed$/.test(name)) && value < 1) return 'critical';
  if ((name === 'nvme.critical_warning' || /^nvme\.[^.]+\.critical_warning$/.test(name)) && value >= 1) return 'critical';
  if (name === 'nvme.available_spare_percent' || /^nvme\.[^.]+\.available_spare_percent$/.test(name)) {
    if (value <= 10) return 'critical';
    if (value <= 20) return 'watch';
  }
  if (name === 'nvme.percentage_used_percent' || /^nvme\.[^.]+\.percentage_used_percent$/.test(name)) {
    if (value >= 90) return 'critical';
    if (value >= 75) return 'watch';
  }
  if (name === 'nvme.media_errors' || /^nvme\.[^.]+\.media_errors$/.test(name)) {
    if (value >= 10) return 'critical';
    if (value > 0) return 'watch';
  }
  if (name === 'wifi.signal_dbm' || /^wifi\.[^.]+\.signal_dbm$/.test(name)) {
    if (value <= -80) return 'critical';
    if (value <= -70) return 'watch';
  }
  if (/^wifi(\.[^.]+)?\.(rx|tx|link)_bitrate_mbps$/.test(name)) {
    if (value <= 12) return 'watch';
  }
  return 'nominal';
}

function metricNamesByPattern(latestMetrics: Record<string, MetricSample>, pattern: RegExp): string[] {
  return Object.keys(latestMetrics)
    .filter((metricName) => pattern.test(metricName))
    .sort(compareLabel);
}

function isWindowsDetail(detail: InvestigationDetail | null): boolean {
  const osName = detail?.fleet_context.device.os_name?.toLowerCase() ?? '';
  return osName.includes('windows');
}

function firstMetricNameByPattern(detail: InvestigationDetail | null, pattern: RegExp): string | null {
  const latestMetrics = detail?.fleet_context.latest_metrics ?? {};
  return metricNamesByPattern(latestMetrics, pattern)[0] ?? null;
}

function keyMetricsForDetail(detail: InvestigationDetail): MetricDefinition[] {
  const metrics: MetricDefinition[] = [];
  const windowsDevice = isWindowsDetail(detail);
  const windowsThermalName = firstMetricNameByPattern(detail, /^thermal\.windows_.*\.temp_c$/);
  const hasCpuTemperature = Boolean(
    latestMetric(detail, 'cpu.package_temp_c')
      || firstMetricNameByPattern(detail, /^cpu\.(?:(?:p|e|lp_e)_)?core_\d+\.temp_c$/),
  );
  const hasWindowsCpuLoad = Boolean(
    latestMetric(detail, 'cpu.load_percent')
      || firstMetricNameByPattern(detail, /^cpu\.(?:(?:p|e|lp_e)_)?core_\d+\.load_percent$/),
  );

  if (hasCpuTemperature || !windowsDevice) {
    metrics.push(windowsDevice && !latestMetric(detail, 'cpu.package_temp_c') ? windowsCpuTemperatureMetric() : baseKeyMetrics[0]);
  }
  if (windowsDevice && windowsThermalName) {
    metrics.push(windowsThermalMetric(windowsThermalName));
  }

  if (hasWindowsCpuLoad) {
    metrics.push(windowsCpuLoadMetric);
  } else if (latestMetric(detail, 'cpu.load_1m') || !windowsDevice) {
    metrics.push(baseKeyMetrics[1]);
  }
  if (
    latestMetric(detail, 'nvme.temp_c')
    || latestMetric(detail, 'nvme.capacity_bytes')
    || firstMetricNameByPattern(detail, /^nvme\.[^.]+\.(temp_c|capacity_bytes|smart_passed|available_spare_percent)$/)
  ) {
    metrics.push(baseKeyMetrics[2]);
  }
  if (latestMetric(detail, 'wifi.signal_dbm') || firstMetricNameByPattern(detail, /^wifi\.[^.]+\.(signal_dbm|rx_bitrate_mbps|tx_bitrate_mbps|link_bitrate_mbps)$/)) {
    metrics.push(baseKeyMetrics[3]);
  }
  return metrics;
}

function cpuProfileValue(detail: InvestigationDetail | null): string {
  const physicalCores = latestMetric(detail, 'cpu.physical_cores');
  const logicalThreads = latestMetric(detail, 'cpu.logical_threads');
  if (physicalCores && logicalThreads) {
    return `${physicalCores.value.toFixed(0)} cores / ${logicalThreads.value.toFixed(0)} threads`;
  }
  if (logicalThreads) return `${logicalThreads.value.toFixed(0)} threads`;
  return detail?.fleet_context.device.cpu_model ? compactCpuModel(detail.fleet_context.device.cpu_model) : 'Unavailable';
}

function cpuProfileStatus(detail: InvestigationDetail | null): SignalStatus {
  return detail?.fleet_context.device.cpu_model || latestMetric(detail, 'cpu.logical_threads') ? 'nominal' : 'missing';
}

function cpuProfileSummary(detail: InvestigationDetail | null): string {
  const model = compactCpuModel(detail?.fleet_context.device.cpu_model);
  const pCores = latestMetric(detail, 'cpu.performance_cores')?.value;
  const eCores = latestMetric(detail, 'cpu.efficient_cores')?.value;
  const lpECores = latestMetric(detail, 'cpu.low_power_efficient_cores')?.value;
  const physicalCores = latestMetric(detail, 'cpu.physical_cores')?.value;
  const logicalThreads = latestMetric(detail, 'cpu.logical_threads')?.value;
  const topology = pCores !== undefined && eCores !== undefined && lpECores !== undefined
    ? `Topology: P ${pCores.toFixed(0)}, E ${eCores.toFixed(0)}, LP-E ${lpECores.toFixed(0)}.`
    : pCores !== undefined && eCores !== undefined
      ? `Topology: P ${pCores.toFixed(0)}, E ${eCores.toFixed(0)}.`
    : physicalCores !== undefined || logicalThreads !== undefined
      ? `Topology: ${physicalCores?.toFixed(0) ?? '?'} cores, ${logicalThreads?.toFixed(0) ?? '?'} threads.`
      : 'Topology metrics are unavailable.';
  return `${model}. ${topology}`;
}

function wifiLinkValue(detail: InvestigationDetail | null): string {
  const rx = latestMetric(detail, 'wifi.rx_bitrate_mbps');
  const tx = latestMetric(detail, 'wifi.tx_bitrate_mbps');
  const link = latestMetric(detail, 'wifi.link_bitrate_mbps');
  if (rx && tx) return `Rx ${metricSampleValue(rx)} / Tx ${metricSampleValue(tx)}`;
  if (rx) return `Rx ${metricSampleValue(rx)}`;
  if (tx) return `Tx ${metricSampleValue(tx)}`;
  if (link) return `Link ${metricSampleValue(link)}`;
  return 'Unavailable';
}

function wifiLinkStatus(detail: InvestigationDetail | null): SignalStatus {
  return strongestStatus(
    metricStatus(detail, 'wifi.rx_bitrate_mbps'),
    metricStatus(detail, 'wifi.tx_bitrate_mbps'),
    metricStatus(detail, 'wifi.link_bitrate_mbps'),
  );
}

function nvmeCapacityValue(detail: InvestigationDetail | null): string {
  return metricValue(detail, 'nvme.capacity_bytes');
}

function nvmeCapacityStatus(detail: InvestigationDetail | null): SignalStatus {
  return latestMetric(detail, 'nvme.capacity_bytes') ? 'nominal' : 'missing';
}

function nvmeIoValue(detail: InvestigationDetail | null): string {
  const read = latestMetric(detail, 'nvme.read_bytes_per_sec');
  const write = latestMetric(detail, 'nvme.write_bytes_per_sec');
  if (read && write) return `R ${metricSampleValue(read)} / W ${metricSampleValue(write)}`;
  return 'Needs 2 samples';
}

function nvmeIoStatus(detail: InvestigationDetail | null): SignalStatus {
  return latestMetric(detail, 'nvme.read_bytes_per_sec') || latestMetric(detail, 'nvme.write_bytes_per_sec') ? 'nominal' : 'missing';
}

function thermalSensorName(detail: InvestigationDetail | null): string | null {
  if (latestMetric(detail, 'cpu.package_temp_c')) return 'cpu.package_temp_c';
  return firstMetricNameByPattern(detail, /^thermal\.windows_.*\.temp_c$/)
    ?? firstMetricNameByPattern(detail, /^thermal\..*\.temp_c$/);
}

function thermalSensorValue(detail: InvestigationDetail | null): string {
  const metricName = thermalSensorName(detail);
  return metricName ? metricValue(detail, metricName) : 'Unavailable';
}

function thermalSensorStatus(detail: InvestigationDetail | null): SignalStatus {
  const metricName = thermalSensorName(detail);
  return metricName ? metricStatus(detail, metricName) : 'missing';
}

function metricBreakdown(detail: InvestigationDetail, name: string): MetricBreakdown | null {
  const latestMetrics = detail.fleet_context.latest_metrics;
  if (name === 'cpu.package_temp_c') {
    const coreBreakdown = cpuCoreBreakdown(detail);
    const coreTypeGroups = coreTypeGroupsForUltra5_125H(coreBreakdown);
    const cores = coreBreakdown.map((core) => {
      const value = breakdownSampleValue(core.sample);
      const group = core.group ?? coreTypeGroups.get(core.index);
      return {
        key: core.key,
        label: core.index,
        value,
        status: core.status,
        ariaLabel: group ? `CPU ${group} core ${core.index} temperature: ${value}` : `CPU core ${core.index} temperature: ${value}`,
        group,
      };
    });
    return {
      title: 'Cores',
      items: cores,
      emptyLabel: 'No core sensors',
      emptyAriaLabel: 'CPU core temperatures: no per-core sensors reported',
    };
  }
  if (name === 'cpu.load_1m') {
    const windows = [
      ['1m', 'cpu.load_1m'],
      ['5m', 'cpu.load_5m'],
      ['15m', 'cpu.load_15m'],
    ].map(([label, metricName]) => {
      const sample = latestMetrics[metricName];
      const value = breakdownSampleValue(sample);
      return {
        key: metricName,
        label,
        value,
        status: statusForMetricSample(metricName, sample),
        ariaLabel: `Load average ${label}: ${value}`,
      };
    });
    return { title: 'Load', items: windows };
  }
  if (name === 'cpu.load_percent') {
    const loads = cpuLoadBreakdown(detail).map((core) => {
      const value = breakdownSampleValue(core.sample);
      return {
        key: core.key,
        label: core.index,
        value,
        status: core.status,
        ariaLabel: core.group ? `CPU ${core.group} core ${core.index} load: ${value}` : `CPU core ${core.index} load: ${value}`,
        group: core.group,
      };
    });
    return {
      title: 'Core load',
      items: loads,
      emptyLabel: 'No core load sensors',
      emptyAriaLabel: 'CPU core loads: no per-core load sensors reported',
    };
  }
  if (name === 'nvme.temp_c') {
    const namespaceNames = new Set<string>();
    const controllerTempNames = new Set<string>();
    for (const metricName of Object.keys(latestMetrics)) {
      const match = metricName.match(/^nvme\.([^.]+)\.(temp_c|capacity_bytes|read_bytes_per_sec|write_bytes_per_sec)$/);
      if (!match) continue;
      if (match[2] === 'temp_c') {
        controllerTempNames.add(match[1]);
      } else {
        namespaceNames.add(match[1]);
      }
    }
    const displayNames = namespaceNames.size > 0
      ? [...namespaceNames, ...[...controllerTempNames].filter((deviceName) => ![...namespaceNames].some((namespaceName) => namespaceName.startsWith(deviceName)))]
      : [...controllerTempNames];
    const devices = displayNames
      .map((deviceName) => {
        const controllerName = deviceName.match(/^(nvme\d+)n\d+$/)?.[1] ?? deviceName;
        const tempName = latestMetrics[`nvme.${deviceName}.temp_c`]
          ? `nvme.${deviceName}.temp_c`
          : `nvme.${controllerName}.temp_c`;
        const capacityName = `nvme.${deviceName}.capacity_bytes`;
        const readName = `nvme.${deviceName}.read_bytes_per_sec`;
        const writeName = `nvme.${deviceName}.write_bytes_per_sec`;
        const parts = [
          latestMetrics[tempName] ? breakdownSampleValue(latestMetrics[tempName]) : null,
          latestMetrics[capacityName] ? breakdownSampleValue(latestMetrics[capacityName]) : null,
          latestMetrics[readName] ? `R ${breakdownSampleValue(latestMetrics[readName])}` : null,
          latestMetrics[writeName] ? `W ${breakdownSampleValue(latestMetrics[writeName])}` : null,
        ].filter((part): part is string => Boolean(part));
        const value = parts.length > 0 ? parts.join(' · ') : '-';
        return {
          key: deviceName,
          label: deviceName,
          value,
          status: statusForMetricSample(tempName, latestMetrics[tempName]),
          ariaLabel: `NVMe ${deviceName}: ${value}`,
        };
      })
      .sort((left, right) => compareLabel(left.label, right.label));
    if (devices.length === 0 && latestMetrics['nvme.temp_c']) {
      const sample = latestMetrics['nvme.temp_c'];
      const value = breakdownSampleValue(sample);
      devices.push({
        key: 'nvme.temp_c',
        label: 'Primary',
        value,
        status: statusForMetricSample('nvme.temp_c', sample),
        ariaLabel: `NVMe primary temperature: ${value}`,
      });
    }
    return {
      title: 'Devices',
      items: devices,
      emptyLabel: 'No NVMe devices',
      emptyAriaLabel: 'NVMe devices: no per-device sensor reported',
    };
  }
  if (name === 'wifi.signal_dbm') {
    const interfaceNames = new Set<string>();
    for (const metricName of Object.keys(latestMetrics)) {
      const match = metricName.match(/^wifi\.([^.]+)\.(signal_dbm|rx_bitrate_mbps|tx_bitrate_mbps|link_bitrate_mbps)$/);
      if (match) interfaceNames.add(match[1]);
    }
    const interfaces = [...interfaceNames]
      .map((interfaceName) => {
        const signalName = `wifi.${interfaceName}.signal_dbm`;
        const rxName = `wifi.${interfaceName}.rx_bitrate_mbps`;
        const txName = `wifi.${interfaceName}.tx_bitrate_mbps`;
        const linkName = `wifi.${interfaceName}.link_bitrate_mbps`;
        const parts = [
          latestMetrics[signalName] ? breakdownSampleValue(latestMetrics[signalName]) : null,
          latestMetrics[rxName] ? `Rx ${breakdownSampleValue(latestMetrics[rxName])}` : null,
          latestMetrics[txName] ? `Tx ${breakdownSampleValue(latestMetrics[txName])}` : null,
          latestMetrics[linkName] && !latestMetrics[rxName] && !latestMetrics[txName] ? `Link ${breakdownSampleValue(latestMetrics[linkName])}` : null,
        ].filter((part): part is string => Boolean(part));
        const value = parts.length > 0 ? parts.join(' · ') : '-';
        return {
          key: interfaceName,
          label: interfaceName,
          value,
          status: statusForMetricSample(signalName, latestMetrics[signalName]),
          ariaLabel: `Wi-Fi ${interfaceName}: ${value}`,
        };
      })
      .sort((left, right) => compareLabel(left.label, right.label));
    if (interfaces.length === 0 && latestMetrics['wifi.signal_dbm']) {
      const sample = latestMetrics['wifi.signal_dbm'];
      const value = breakdownSampleValue(sample);
      interfaces.push({
        key: 'wifi.signal_dbm',
        label: 'Primary',
        value,
        status: statusForMetricSample('wifi.signal_dbm', sample),
        ariaLabel: `Wi-Fi primary signal: ${value}`,
      });
    }
    return {
      title: 'Interfaces',
      items: interfaces,
      emptyLabel: 'No Wi-Fi interfaces',
      emptyAriaLabel: 'Wi-Fi interfaces: no per-interface signal reported',
    };
  }
  if (/^thermal\.windows_.*\.temp_c$/.test(name)) {
    const zones = metricNamesByPattern(latestMetrics, /^thermal\.windows_.*\.temp_c$/)
      .map((metricName) => {
        const sample = latestMetrics[metricName];
        const label = metricName
          .replace(/^thermal\.windows_/, '')
          .replace(/\.temp_c$/, '');
        const value = breakdownSampleValue(sample);
        return {
          key: metricName,
          label,
          value,
          status: statusForMetricSample(metricName, sample),
          ariaLabel: `Windows thermal zone ${label}: ${value}`,
        };
      });
    return {
      title: 'Zones',
      items: zones,
      emptyLabel: 'No thermal zones',
      emptyAriaLabel: 'Windows thermal zones: no zones reported',
    };
  }
  return null;
}

function metricStatus(detail: InvestigationDetail | null, name: string): SignalStatus {
  if (name === 'cpu.package_temp_c' && !latestMetric(detail, name)) {
    const samples = cpuTemperatureSamples(detail);
    if (samples.length === 0) return 'missing';
    return strongestStatus(...samples.map(coreTemperatureStatus));
  }
  return statusForMetricSample(name, latestMetric(detail, name));
}

function statusLabel(status: SignalStatus): string {
  return {
    nominal: 'Nominal',
    watch: 'Watch',
    critical: 'Critical',
    missing: 'No data',
  }[status];
}

function looksCorruptText(value: string): boolean {
  const replacementCount = [...value].filter((char) => char === '\uFFFD' || char === '�').length;
  if (replacementCount >= 2) return true;
  return /(?:���|����|占쏙옙|Ã.|Â.|ì.|ë.|í.)/.test(value);
}

function cleanDisplayText(value: string | null | undefined, fallback: string): string {
  if (!value) return fallback;
  return looksCorruptText(value) ? fallback : value;
}

function cleanTimelineSummary(value: string | null | undefined): string {
  return cleanDisplayText(value, 'Windows event message was hidden because its source text encoding was corrupt.');
}

function cleanInvestigationDetail(detail: InvestigationDetail): InvestigationDetail {
  return {
    ...detail,
    item: {
      ...detail.item,
      evidence: cleanDisplayText(detail.item.evidence, 'Evidence text was hidden because its source encoding was corrupt.'),
      why_now: cleanDisplayText(detail.item.why_now, 'Reason text was hidden because its source encoding was corrupt.'),
      next_step: cleanDisplayText(detail.item.next_step, 'Review the current telemetry and recent events for this device.'),
    },
    timeline: detail.timeline.map((event) => ({
      ...event,
      summary: cleanTimelineSummary(event.summary),
    })),
    report: {
      ...detail.report,
      summary: cleanDisplayText(detail.report.summary, 'Report text was hidden because its source encoding was corrupt.'),
      recommended_next_step: cleanDisplayText(detail.report.recommended_next_step, 'Review current telemetry and recent events.'),
    },
    verification: {
      ...detail.verification,
      summary: cleanDisplayText(detail.verification.summary, 'Verification text was hidden because its source encoding was corrupt.'),
    },
  };
}

function eventCountValue(events: InvestigationDetail['timeline'], scope: string): string {
  if (events.length === 1) return `1 ${scope} event`;
  return `${events.length} ${scope} events`;
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
      || latestMetric(detail, 'nvme.smart_passed')
      || latestMetric(detail, 'nvme.available_spare_percent')
      || latestMetric(detail, 'nvme.percentage_used_percent')
      || latestMetric(detail, 'nvme.media_errors'),
  );
  if (!hasSignal) return 'missing';
  return strongestStatus(
    metricStatus(detail, 'nvme.critical_warning'),
    metricStatus(detail, 'nvme.smart_passed'),
    metricStatus(detail, 'nvme.available_spare_percent'),
    metricStatus(detail, 'nvme.percentage_used_percent'),
    metricStatus(detail, 'nvme.media_errors'),
  );
}

function nvmeHealthValue(detail: InvestigationDetail | null): string {
  const criticalWarning = latestMetric(detail, 'nvme.critical_warning');
  if (criticalWarning && criticalWarning.value >= 1) return 'Critical warning';
  const smartPassed = latestMetric(detail, 'nvme.smart_passed');
  if (smartPassed && smartPassed.value < 1) return 'SMART failed';
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
  const windowsDevice = isWindowsDetail(detail);
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
  const wifiInterfaceNames = metricNamesByPattern(detail?.fleet_context.latest_metrics ?? {}, /^wifi\.[^.]+\.signal_dbm$/)
    .map((metricName) => metricName.split('.')[1]);
  const nvmeDeviceNames = metricNamesByPattern(detail?.fleet_context.latest_metrics ?? {}, /^nvme\.[^.]+\.capacity_bytes$/)
    .map((metricName) => metricName.split('.')[1]);

  const tiles: TelemetryTile[] = [
    {
      id: 'cpu.profile',
      category: 'Hardware',
      label: 'CPU Profile',
      value: cpuProfileValue(detail),
      status: cpuProfileStatus(detail),
      summary: cpuProfileSummary(detail),
      Icon: Cpu,
    },
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
      value: latestMetric(detail, 'disk.root_used_percent') ? metricValue(detail, 'disk.root_used_percent') : eventCountValue(storageEvents, 'storage'),
      status: storageStatus,
      summary: 'root filesystem 사용률과 kernel storage warning을 함께 봅니다. (disk fullness and I/O stalls)',
      Icon: HardDrive,
    },
    {
      id: 'nvme.capacity',
      category: 'Storage',
      label: 'NVMe Capacity',
      value: nvmeCapacityValue(detail),
      status: nvmeCapacityStatus(detail),
      summary: nvmeDeviceNames.length > 0
        ? `Detected NVMe namespace(s): ${nvmeDeviceNames.join(', ')}. Capacity uses sysfs block size in bytes.`
        : 'NVMe capacity is unavailable from sysfs.',
      Icon: HardDrive,
    },
    {
      id: 'nvme.io',
      category: 'Storage',
      label: 'NVMe I/O',
      value: nvmeIoValue(detail),
      status: nvmeIoStatus(detail),
      summary: 'Read/write throughput is calculated from NVMe sector counters between collector samples. 첫 샘플에는 비교 기준이 없어 비어 있을 수 있습니다.',
      Icon: Gauge,
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
      id: 'thermal.sensor',
      category: 'Thermal',
      label: windowsDevice ? 'Windows Thermal' : 'Thermal Sensor',
      value: thermalSensorValue(detail),
      status: thermalSensorStatus(detail),
      summary: windowsDevice
        ? 'Windows가 실제로 노출한 thermal zone 또는 sensor 값입니다. CPU package/core 온도로 강제 변환하지 않습니다.'
        : 'collector가 받은 CPU package 또는 thermal zone 값을 보여줍니다.',
      Icon: Thermometer,
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
      id: 'wifi.link',
      category: 'Network',
      label: 'Wi-Fi Link',
      value: wifiLinkValue(detail),
      status: wifiLinkStatus(detail),
      summary: wifiInterfaceNames.length > 0
        ? `iw or iwconfig link bitrate for ${wifiInterfaceNames.join(', ')}. 실제 인터넷 속도 측정값이 아니라 AP와의 무선 링크 속도입니다.`
        : 'Wi-Fi link bitrate is unavailable.',
      Icon: Wifi,
    },
    {
      id: 'network.events',
      category: 'Network',
      label: 'Network Events',
      value: eventCountValue(networkEvents, 'network'),
      status: networkEvents.length > 0 ? 'watch' : 'nominal',
      summary: 'reconnect, carrier loss, NetworkManager warning이 조사 흐름에 포함됐는지 봅니다.',
      Icon: Network,
    },
    {
      id: 'network.reconnects',
      category: 'Network',
      label: 'Reconnect History',
      value: eventCountValue(reconnectEvents, 'reconnect'),
      status: reconnectEvents.length > 0 ? 'watch' : 'nominal',
      summary: 'Wi-Fi disconnect/reconnect 흐름이 반복되는지 직접 확인합니다. (reconnect history)',
      Icon: Wifi,
    },
    {
      id: 'thermal.throttling',
      category: 'Thermal',
      label: 'Thermal Throttling',
      value: eventCountValue(throttlingEvents, 'thermal'),
      status: throttlingEvents.length > 0 ? 'watch' : 'nominal',
      summary: 'kernel thermal throttling이나 threshold event가 실제로 발생했는지 봅니다.',
      Icon: Thermometer,
    },
    {
      id: 'kernel.warnings',
      category: 'Reliability',
      label: 'Kernel Warnings',
      value: eventCountValue(kernelWarnings, 'kernel'),
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
  if (latestMetric(detail, 'cpu.load_percent')) {
    tiles.splice(1, 0, {
      id: 'cpu.load_percent',
      category: 'Compute',
      label: 'CPU Core Load',
      value: metricValue(detail, 'cpu.load_percent'),
      status: metricStatus(detail, 'cpu.load_percent'),
      summary: 'LibreHardwareMonitor/OpenHardwareMonitor가 보낸 Windows CPU total/core별 사용률입니다. Linux load average와 다른 percent metric입니다.',
      Icon: Cpu,
    });
  }
  if (!windowsDevice) return tiles;
  return tiles.filter((tile) => {
    if (tile.status !== 'missing') return true;
    return !['fan.rpm', 'thermal.sensor'].includes(tile.id);
  });
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

function sourceLabelForItem(detail: InvestigationDetail | null, item: InvestigationItem | null | undefined): string | null {
  const sourceItem = detail?.item ?? item;
  if (!sourceItem) return null;
  const deviceLabel = detail
    ? deviceDisplayLabel(detail.fleet_context.device)
    : itemDeviceDisplayLabel(sourceItem);
  return `${deviceLabel} / ${sourceItem.category}`;
}

function deviceDisplayLabel(device: { display_name?: string | null; hostname: string }): string {
  const alias = device.display_name?.trim();
  if (alias && alias !== device.hostname) return `${alias} · ${device.hostname}`;
  return alias || device.hostname;
}

function itemDeviceDisplayLabel(item: { device_display_name?: string | null; device_hostname: string }): string {
  const alias = item.device_display_name?.trim();
  if (alias && alias !== item.device_hostname) return `${alias} · ${item.device_hostname}`;
  return alias || item.device_hostname;
}

function riskChipLabel(level: RiskLevel | undefined, detail: InvestigationDetail | null, item: InvestigationItem | null | undefined): string {
  if (!level) return 'No risk';
  const category = detail?.item.category ?? item?.category;
  return category ? `${riskLabels[level]} · ${category}` : riskLabels[level];
}

function selectedRiskSourceDescription(
  level: RiskLevel | undefined,
  detail: InvestigationDetail | null,
  item: InvestigationItem | null | undefined,
): string | null {
  const sourceItem = detail?.item ?? item;
  const source = sourceLabelForItem(detail, item);
  if (!level || !sourceItem || !source) return null;
  return `선택된 ${level} 출처: ${source} - ${sourceItem.title}.`;
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
  description: string | string[];
  helpId: string;
  Icon: typeof Activity;
  label: string;
  title: string;
}) {
  return (
    <span aria-describedby={helpId} className={['status-chip', 'explainable', 'explain-left', className].filter(Boolean).join(' ')} tabIndex={0}>
      <Icon aria-hidden="true" />
      <span className="status-chip-label">{label}</span>
      <span className="status-tooltip explain-popover" id={helpId} role="tooltip">
        <strong>{title}</strong>
        {Array.isArray(description)
          ? description.map((line) => <span key={line}>{line}</span>)
          : <span>{description}</span>}
      </span>
    </span>
  );
}

function ProductInfoChip() {
  return (
    <span
      aria-describedby="project-info-help"
      className="meta-chip product-info-chip explainable explain-left"
      tabIndex={0}
    >
      <Info aria-hidden="true" />
      Project info
      <span className="product-info-tooltip explain-popover" id="project-info-help" role="tooltip">
        <strong>Metadata</strong>
        <span className="product-info-line">
          <UserRound aria-hidden="true" />
          <a href="https://github.com/chquandogong/CHENGHAO-QUAN" target="_blank" rel="noreferrer">
            Made by Dr. 권성호
          </a>
        </span>
        <span className="product-info-line">
          <Info aria-hidden="true" />
          About: workstation health investigation
        </span>
        <span className="product-info-line">
          <Tag aria-hidden="true" />
          Version {appVersion}
        </span>
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

function MetricBreakdownChip({ item }: { item: MetricBreakdownItem }) {
  return (
    <span
      aria-label={item.ariaLabel}
      className={`breakdown-chip breakdown-${item.status}`}
    >
      <strong>{item.label}</strong>
      <span>{item.value}</span>
    </span>
  );
}

function MetricBreakdownView({ breakdown }: { breakdown: MetricBreakdown }) {
  const ariaLabel = breakdown.items.length > 0
    ? `${breakdown.title}: ${breakdown.items.map((item) => `${item.label} ${item.value}`).join(', ')}`
    : `${breakdown.title}: ${breakdown.emptyLabel ?? 'No data'}`;
  const groupedItems = breakdown.items.reduce<Map<string, MetricBreakdownItem[]>>((groups, item) => {
    if (!item.group) return groups;
    const group = groups.get(item.group) ?? [];
    group.push(item);
    groups.set(item.group, group);
    return groups;
  }, new Map());
  const hasGroups = groupedItems.size > 0;
  const groupOrder = ['P', 'E', 'LP-E'];
  return (
    <span aria-label={ariaLabel} className="metric-breakdown metric-chip-breakdown">
      <span className="metric-breakdown-title">{breakdown.title}</span>
      {hasGroups
        ? groupOrder
          .filter((group) => groupedItems.has(group))
          .map((group) => (
            <span
              aria-label={`${group} core group: ${groupedItems.get(group)?.map((item) => `${item.label} ${item.value}`).join(', ')}`}
              className="breakdown-group"
              key={group}
            >
              <span className="breakdown-group-label">{group}</span>
              {groupedItems.get(group)?.map((item) => <MetricBreakdownChip item={item} key={item.key} />)}
            </span>
          ))
        : breakdown.items.map((item) => <MetricBreakdownChip item={item} key={item.key} />)}
      {breakdown.items.length === 0 && (
        <span
          aria-label={breakdown.emptyAriaLabel ?? `${breakdown.title}: No data`}
          className="breakdown-chip breakdown-missing"
        >
          <strong>{breakdown.emptyLabel ?? 'No data'}</strong>
        </span>
      )}
    </span>
  );
}

function MetricRow({ detail, metric }: { detail: InvestigationDetail; metric: MetricDefinition }) {
  const status = metricStatus(detail, metric.name);
  const breakdown = metricBreakdown(detail, metric.name);
  return (
    <div className={`metric-row metric-${metric.tone} signal-${status}`}>
      <div className="metric-topline">
        <dt className="metric-name">
          <metric.Icon aria-hidden="true" />
          {metric.label}
        </dt>
        <div className="metric-help explainable explain-left">
          <button aria-describedby={`${metric.name}-help`} aria-label={`Explain ${metric.ariaLabel} metric`} type="button">
            <HelpCircle aria-hidden="true" />
          </button>
          <div className="metric-tooltip explain-popover" id={`${metric.name}-help`} role="tooltip">
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
      {breakdown && <MetricBreakdownView breakdown={breakdown} />}
    </div>
  );
}

function MetricLedger({ detail }: { detail: InvestigationDetail }) {
  const metrics = keyMetricsForDetail(detail);
  return (
    <dl className="metric-ledger" aria-label="Core telemetry details">
      {metrics.map((metric) => (
        <MetricRow detail={detail} key={metric.name} metric={metric} />
      ))}
    </dl>
  );
}

function TelemetryBrief({ detail }: { detail: InvestigationDetail | null }) {
  if (!detail) return null;
  const metrics = keyMetricsForDetail(detail);
  return (
    <section className="telemetry-brief" aria-label="Telemetry Brief">
      <span className="brief-title">Telemetry Brief</span>
      <div className="brief-readings">
      {metrics.map((metric) => {
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
  const observedCount = tiles.filter((tile) => tile.status !== 'missing').length;
  const missingLabels = tiles.filter((tile) => tile.status === 'missing').map((tile) => tile.label);
  const windowsDevice = isWindowsDetail(detail);
  return (
    <section className="telemetry-matrix" aria-label="Telemetry coverage matrix">
      <div className="matrix-head">
        <div>
          <h3>Telemetry Matrix</h3>
          <p>CPU profile, fan, NVMe health/capacity/I/O, disk, battery, Wi-Fi link, memory, network, kernel, agent freshness를 한 번에 확인합니다.</p>
        </div>
        <span
          aria-describedby="telemetry-coverage-help"
          className="coverage-chip explainable explain-left"
          tabIndex={0}
        >
          {observedCount}/{tiles.length} observed
          <span className="coverage-tooltip explain-popover" id="telemetry-coverage-help" role="tooltip">
            <strong>Telemetry coverage</strong>
            <span>{windowsDevice
              ? 'Windows view는 현재 장비가 실제로 보낸 신호 중심으로 구성합니다. 노출되지 않은 Linux식 센서는 억지로 결측 표시하지 않습니다.'
              : '관측된 범주 수입니다. 위험 점수가 아니라, 조사에 필요한 자료가 얼마나 들어왔는지 보여줍니다.'}</span>
            <span>{missingLabels.length > 0 ? `Missing: ${missingLabels.join(', ')}` : 'Missing: none'}</span>
          </span>
        </span>
      </div>
      <div className="telemetry-grid">
        {tiles.map((tile) => (
          <article
            aria-describedby={`telemetry-${tile.id}-help`}
            className={`telemetry-tile signal-${tile.status} explainable explain-left`}
            key={tile.id}
            tabIndex={0}
          >
            <span className="telemetry-category">{tile.category}</span>
            <div className="telemetry-value">
              <tile.Icon aria-hidden="true" />
              <strong>{tile.value}</strong>
            </div>
            <h4>{tile.label}</h4>
            <p className="telemetry-summary explain-popover" id={`telemetry-${tile.id}-help`} role="tooltip">
              <strong>Explanation</strong>
              <span>{tile.summary}</span>
            </p>
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
  const operationCards = [
    {
      id: 'agent-freshness',
      Icon: Clock3,
      label: 'Agent Freshness',
      value: stale > 0 ? `${stale} stale` : 'Fresh',
      summary: detail?.fleet_context.device.last_seen_at ? `Last selected batch ${new Date(detail.fleet_context.device.last_seen_at).toLocaleString()}` : 'Waiting for selected device context.',
      status: stale > 0 ? 'watch' : 'nominal',
    },
    {
      id: 'offline-buffer',
      Icon: HardDrive,
      label: 'Offline Buffer',
      value: 'Spool-ready',
      summary: 'Collector batches can queue locally during server or network outage.',
      status: 'nominal',
    },
    {
      id: 'enrollment-guard',
      Icon: ShieldCheck,
      label: 'Enrollment Guard',
      value: 'Device-bound',
      summary: 'Agent tokens can be created, rotated, and revoked per device.',
      status: 'nominal',
    },
    {
      id: 'pattern-radar',
      Icon: FileSearch,
      label: 'Pattern Radar',
      value: `${patternCount} events`,
      summary: `${patterns?.category_groups[0]?.category ?? 'No repeated category'} is the leading grouped signal.`,
      status: patternCount > 0 ? 'watch' : 'missing',
    },
  ] satisfies {
    id: string;
    Icon: typeof Activity;
    label: string;
    value: string;
    summary: string;
    status: SignalStatus;
  }[];
  return (
    <section className="operations-rail" aria-label="Operations Rail">
      {operationCards.map((card) => (
        <article
          aria-describedby={`ops-${card.id}-help`}
          className={`ops-card signal-${card.status} explainable explain-left`}
          key={card.id}
          tabIndex={0}
        >
          <span className="ops-label"><card.Icon aria-hidden="true" /> {card.label}</span>
          <strong>{card.value}</strong>
          <p className="ops-summary explain-popover" id={`ops-${card.id}-help`} role="tooltip">
            <strong>Explanation</strong>
            <span>{card.summary}</span>
          </p>
        </article>
      ))}
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
              'explainable',
              'explain-up',
              'explain-center',
              isActive ? 'active' : '',
              isComplete ? 'complete' : '',
            ].filter(Boolean).join(' ')}
            key={flowStage}
            tabIndex={0}
          >
            <span aria-hidden="true">{flowStage[0]}</span>
            <span className="workflow-step-tooltip explain-popover" role="tooltip">
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

function FleetBrief({ overview, queue }: { overview: FleetOverview | null; queue: InvestigationItem[] }) {
  const summary = overview?.summary;
  const leadingSource = queue.find((item) => item.risk_level === 'critical')
    ?? queue.find((item) => item.risk_level === 'warning')
    ?? queue[0]
    ?? null;
  const stats = [
    {
      description: 'Total은 현재 fleet에서 관측된 장비 수입니다.',
      label: 'Total',
      metricLabel: 'devices',
      singularUnit: 'device',
      pluralUnit: 'devices',
      value: summary?.total ?? 0,
      tone: 'neutral',
    },
    {
      description: 'Critical은 즉시 대응이 필요한 risk 상태의 장비 수입니다.',
      label: 'Critical',
      metricLabel: 'devices',
      singularUnit: 'device',
      pluralUnit: 'devices',
      value: summary?.critical ?? 0,
      tone: 'critical',
    },
    {
      description: 'Warning은 확인이 필요한 risk 상태의 장비 수입니다.',
      label: 'Warning',
      metricLabel: 'devices',
      singularUnit: 'device',
      pluralUnit: 'devices',
      value: summary?.warning ?? 0,
      tone: 'warning',
    },
    {
      description: 'Open은 현재 조사 중인 이슈 수입니다. 장비 수와 다를 수 있습니다.',
      label: 'Open',
      metricLabel: 'issues',
      singularUnit: 'issue',
      pluralUnit: 'issues',
      value: queue.length,
      tone: 'queue',
    },
  ];
  const sourceTone = leadingSource?.risk_level === 'critical'
    ? 'critical'
    : leadingSource?.risk_level === 'warning'
      ? 'warning'
      : 'neutral';

  return (
    <section className="fleet-brief" aria-label="Fleet Brief">
      <span className="brief-title">Fleet Brief</span>
      <div className="fleet-readings">
        {stats.map((stat) => (
          <span
            aria-describedby={`fleet-${stat.label.toLowerCase()}-help`}
            aria-label={`${stat.label} ${stat.metricLabel}: ${stat.value}`}
            className={`fleet-reading fleet-${stat.tone} explainable explain-right`}
            key={stat.label}
            tabIndex={0}
          >
            <strong>{stat.value}</strong>
            <span>{stat.label}</span>
            <small>{stat.value === 1 ? stat.singularUnit : stat.pluralUnit}</small>
            <span className="fleet-tooltip explain-popover" id={`fleet-${stat.label.toLowerCase()}-help`} role="tooltip">
              {stat.description}
            </span>
          </span>
        ))}
      </div>
      <div className={`fleet-source fleet-${sourceTone}`}>
        <span>{leadingSource ? `${riskLabels[leadingSource.risk_level]} source` : 'No active source'}</span>
        <strong>{leadingSource ? `${itemDeviceDisplayLabel(leadingSource)} / ${leadingSource.category}` : 'No active warning'}</strong>
        <em>{leadingSource?.title ?? 'All selected fleet signals are clear.'}</em>
      </div>
    </section>
  );
}

function deviceSnapshotSummary(snapshot: DeviceSnapshot): string {
  const metricCount = Object.keys(snapshot.latest_metrics).length;
  const eventCount = snapshot.recent_events.length;
  const metricLabel = metricCount === 1 ? 'metric' : 'metrics';
  const eventLabel = eventCount === 1 ? 'event' : 'events';
  return `${metricCount} ${metricLabel} / ${eventCount} ${eventLabel}`;
}

function deviceLastSeenLabel(snapshot: DeviceSnapshot): string {
  return `Last seen ${new Date(snapshot.device.last_seen_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
}

function deviceHardwareLabel(snapshot: DeviceSnapshot): string {
  return snapshot.device.cpu_model
    ?? snapshot.device.model
    ?? snapshot.device.os_name
    ?? snapshot.device.kernel_version
    ?? 'Hardware profile pending';
}

function deviceIssues(queue: InvestigationItem[], deviceId: string): InvestigationItem[] {
  return queue.filter((item) => item.device_id === deviceId);
}

function deviceIssueSummary(issues: InvestigationItem[]): string {
  if (issues.length === 0) return 'No active issues';
  if (issues.length === 1) return `1 issue: ${issues[0].title}`;
  return `${issues.length} issues: ${issues[0].title}`;
}

function snapshotToInvestigationDetail(
  snapshot: DeviceSnapshot,
  issues: InvestigationItem[],
): InvestigationDetail {
  const primaryIssue = issues[0];
  const deviceLabel = deviceDisplayLabel(snapshot.device);
  const metricCount = Object.keys(snapshot.latest_metrics).length;
  const fallbackItem: InvestigationItem = {
    id: `${snapshot.device.device_id}:overview`,
    priority: 'Low',
    stage: 'Detect',
    risk_level: snapshot.risk_level,
    device_id: snapshot.device.device_id,
    device_display_name: snapshot.device.display_name,
    device_hostname: snapshot.device.hostname,
    title: issues.length > 0 ? primaryIssue.title : 'Device telemetry overview',
    category: issues.length > 0 ? primaryIssue.category : 'device',
    confidence: issues.length > 0 ? primaryIssue.confidence : 'high',
    why_now: issues.length > 0 ? primaryIssue.why_now : `${deviceLabel} has no active issue.`,
    evidence: issues.length > 0
      ? primaryIssue.evidence
      : `${metricCount} telemetry metric${metricCount === 1 ? '' : 's'} collected. Risk is ${riskLabels[snapshot.risk_level]}.`,
    next_step: issues.length > 0
      ? primaryIssue.next_step
      : 'Review telemetry coverage and recent events for this device.',
    updated_at: snapshot.device.last_seen_at,
  };
  const item = primaryIssue ?? fallbackItem;
  return {
    item,
    timeline: snapshot.recent_events.map((event) => ({
      observed_at: event.observed_at,
      category: event.category,
      severity: event.severity,
      source: event.source,
      summary: event.message_summary,
      raw_ref: event.raw_ref,
    })),
    hypotheses: issues.length > 0
      ? []
      : [
          {
            category: 'device',
            title: 'No active investigation for this device',
            confidence: 'high',
            supporting_evidence: [`${deviceSnapshotSummary(snapshot)} reported by collector.`],
            contradicting_evidence: ['No warning or critical finding is currently queued for this device.'],
            missing_checks: ['Review telemetry coverage to see which hardware signals are unavailable.'],
          },
        ],
    actions: issues.length > 0
      ? []
      : [
          {
            label: 'Review telemetry coverage',
            description: 'Check which CPU, Wi-Fi, NVMe, disk, memory, battery, fan, and event signals are available for this device.',
          },
        ],
    interventions: [],
    verification: {
      status: issues.length > 0 ? 'Pending' : 'No active issues',
      summary: issues.length > 0
        ? 'Open the investigation before recording or verifying an intervention.'
        : `${deviceLabel} has no active issue awaiting verification.`,
      signals: Object.keys(snapshot.latest_metrics).slice(0, 6),
    },
    report: {
      summary: issues.length > 0
        ? `${deviceLabel} has ${deviceIssueSummary(issues)}.`
        : `${deviceLabel} is visible in Devices and currently has no active issue.`,
      recommended_next_step: issues.length > 0
        ? item.next_step
        : 'Use Telemetry Matrix to inspect available and missing signals.',
    },
    fleet_context: snapshot,
  };
}

function FleetDevices({
  onSelect,
  overview,
  queue,
  selectedDeviceId,
}: {
  onSelect: (deviceId: string) => void;
  overview: FleetOverview | null;
  queue: InvestigationItem[];
  selectedDeviceId: string | null;
}) {
  return (
    <section className="panel fleet-devices-panel" aria-label="Devices">
      <div className="panel-head">
        <h2>Devices</h2>
        <span>{overview?.devices.length ?? 0} devices</span>
      </div>
      <div className="fleet-device-list">
        {overview?.devices.length ? (
          overview.devices.map((snapshot) => {
            const issues = deviceIssues(queue, snapshot.device.device_id);
            const selected = snapshot.device.device_id === selectedDeviceId;
            return (
              <button
                aria-pressed={selected}
                className={selected ? 'fleet-device-row selected' : 'fleet-device-row'}
                key={snapshot.device.device_id}
                onClick={() => onSelect(snapshot.device.device_id)}
                type="button"
              >
                <div>
                  <strong>{deviceDisplayLabel(snapshot.device)}</strong>
                  <span>{deviceHardwareLabel(snapshot)}</span>
                  <small>{deviceSnapshotSummary(snapshot)} · {deviceLastSeenLabel(snapshot)}</small>
                  <em>{deviceIssueSummary(issues)}</em>
                </div>
                <span className={riskClass(snapshot.risk_level)}>{riskLabels[snapshot.risk_level]}</span>
              </button>
            );
          })
        ) : (
          <p className="status">No devices reported yet.</p>
        )}
      </div>
    </section>
  );
}

function DeviceIssueList({
  issues,
  selectedId,
  onSelect,
}: {
  issues: InvestigationItem[];
  selectedId: string | null;
  onSelect: (issue: InvestigationItem) => void;
}) {
  return (
    <section className="panel queue-panel" aria-label="Device Issues">
      <div className="panel-head">
        <h2>Device Issues</h2>
        <span>{issues.length} items</span>
      </div>
      <div className="queue-list">
        {issues.length === 0 ? (
          <p className="status">No active investigations for this device.</p>
        ) : (
          issues.map((item) => (
            <button
              className={item.id === selectedId ? 'queue-item selected' : 'queue-item'}
              key={item.id}
              onClick={() => onSelect(item)}
              type="button"
            >
              <span className={priorityClass(item.priority)}>{item.priority}</span>
              <strong>{item.title}</strong>
              <em>{item.why_now}</em>
              <small>{item.next_step}</small>
            </button>
          ))
        )}
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
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
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
        const initialDeviceId = queueData.items[0]?.device_id ?? fleetData.devices[0]?.device.device_id ?? null;
        const initialItemId = initialDeviceId
          ? queueData.items.find((item) => item.device_id === initialDeviceId)?.id ?? null
          : null;
        setOverview(fleetData);
        setQueue(queueData.items);
        setPatterns(patternData);
        setSelectedDeviceId(initialDeviceId);
        setSelectedId(initialItemId);
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
      setNotes([]);
      return;
    }
    let active = true;
    Promise.all([fetchInvestigationDetail(selectedId), fetchInvestigationNotes(selectedId)])
      .then(([detailData, notesData]) => {
        if (!active) return;
        setDetail(cleanInvestigationDetail(detailData));
        setNotes(notesData.notes);
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof Error ? err.message : 'Unknown detail API error');
      });
    return () => {
      active = false;
    };
  }, [selectedId]);

  const selectedSnapshot = useMemo(
    () => overview?.devices.find((snapshot) => snapshot.device.device_id === selectedDeviceId)
      ?? overview?.devices[0]
      ?? null,
    [overview, selectedDeviceId],
  );
  const selectedDeviceIssues = useMemo(
    () => selectedSnapshot ? deviceIssues(queue, selectedSnapshot.device.device_id) : [],
    [queue, selectedSnapshot],
  );
  const selectedItem = useMemo(
    () => queue.find((item) => item.id === selectedId)
      ?? selectedDeviceIssues[0]
      ?? null,
    [queue, selectedDeviceIssues, selectedId],
  );
  const selectedDetail = useMemo(
    () => {
      if (!selectedSnapshot) return null;
      if (detail && detail.fleet_context.device.device_id === selectedSnapshot.device.device_id) {
        return detail;
      }
      return cleanInvestigationDetail(snapshotToInvestigationDetail(selectedSnapshot, selectedDeviceIssues));
    },
    [detail, selectedDeviceIssues, selectedSnapshot],
  );
  const latestVerificationResult = detail?.interventions[detail.interventions.length - 1]?.verification_result;
  const nextAction = selectedDetail?.actions[0];
  const primaryEvidence = selectedDetail?.item.evidence ?? selectedDetail?.timeline[0]?.summary ?? 'Select a device to inspect telemetry.';
  const verificationLabel = detail?.verification.status ?? selectedDetail?.verification.status ?? 'No active issues';
  const verificationSummary = detail?.verification.summary ?? selectedDetail?.verification.summary ?? 'No verification is pending for this device.';
  const selectedStage = selectedItem?.stage ?? 'Detect';
  const selectedRiskLevel = selectedDetail?.item.risk_level ?? selectedSnapshot?.risk_level;
  const deviceLabel = selectedDetail
    ? deviceDisplayLabel(selectedDetail.fleet_context.device)
    : 'No device selected';
  const caseTitle = selectedItem?.title ?? selectedDetail?.item.title ?? 'Select a device';
  const selectedRiskSource = selectedRiskSourceDescription(selectedRiskLevel, selectedDetail, selectedItem);
  const selectedRiskDescription = selectedRiskSource
    ? [riskDescription(selectedRiskLevel), selectedRiskSource]
    : riskDescription(selectedRiskLevel);
  const riskLabel = riskChipLabel(selectedRiskLevel, selectedDetail, selectedItem);
  const whyNow = selectedDetail?.item.evidence ?? selectedItem?.why_now ?? 'Choose a device to see telemetry evidence.';
  const whyDetail = selectedDetail?.item.category === 'agent'
    ? 'Fresh telemetry is required before trusting older thermal, load, or storage readings.'
    : selectedDetail?.hypotheses[0]?.contradicting_evidence[0]
      ?? selectedDetail?.hypotheses[0]?.supporting_evidence[0]
      ?? 'Telemetry appears after selecting a device.';
  const actionLabel = nextAction?.label ?? selectedItem?.next_step ?? 'Review telemetry coverage';
  const actionSummary = nextAction?.description ?? selectedItem?.next_step ?? 'Inspect available and missing signals for the selected device.';
  const proofSummary = latestVerificationResult?.summary ?? verificationSummary;

  function handleSelectDevice(deviceId: string) {
    const firstIssue = queue.find((item) => item.device_id === deviceId) ?? null;
    setSelectedDeviceId(deviceId);
    setSelectedId(firstIssue?.id ?? null);
    setDetail(null);
    setNotes([]);
  }

  function handleSelectIssue(issue: InvestigationItem) {
    setSelectedDeviceId(issue.device_id);
    setSelectedId(issue.id);
    setDetail(null);
    setNotes([]);
  }

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
          <div className="meta-chips" aria-label="Project metadata">
            <ProductInfoChip />
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
              label={selectedItem?.priority ?? 'No active issue'}
              title="Priority / 우선순위"
            />
            <StatusChip
              className={selectedRiskLevel ? riskClass(selectedRiskLevel) : 'status-neutral'}
              description={selectedRiskDescription}
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

        <TelemetryBrief detail={selectedDetail} />

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
          <FleetBrief overview={overview} queue={queue} />
          <WorkflowRail actionLabel={actionLabel} proofSummary={proofSummary} stage={selectedStage} />
        </div>
      </section>

      <OperationsRail overview={overview} patterns={patterns} detail={selectedDetail} />

      <section className="investigation-layout">
        <aside className="side-stack">
          <FleetDevices
            onSelect={handleSelectDevice}
            overview={overview}
            queue={queue}
            selectedDeviceId={selectedSnapshot?.device.device_id ?? selectedDeviceId}
          />
          <DeviceIssueList issues={selectedDeviceIssues} selectedId={selectedId} onSelect={handleSelectIssue} />
        </aside>

        <section className="detail-grid">
          <article className="panel hero-panel">
            <div className="panel-head">
              <h2>{selectedDetail?.item.title ?? 'Select a device'}</h2>
              {selectedDetail && <span className={riskClass(selectedDetail.item.risk_level)}>{riskLabels[selectedDetail.item.risk_level]}</span>}
            </div>
            <p className="lead">{selectedDetail?.item.evidence ?? 'Choose a device from the list.'}</p>
            {selectedDetail && <MetricLedger detail={selectedDetail} />}
            <TelemetryMatrix detail={selectedDetail} overview={overview} />
          </article>

          <article className="panel collapsible-panel" id="evidence-panel" tabIndex={-1}>
            <div className="panel-head">
              <h2>Evidence timeline</h2>
              <span>{selectedDetail?.timeline.length ?? 0} events</span>
            </div>
            <p className="panel-summary">{selectedDetail?.timeline[0]?.summary ?? 'No events selected.'}</p>
            <div className="panel-body timeline">
              {selectedDetail?.timeline.map((event) => (
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
              <span>{selectedDetail?.hypotheses.length ?? 0}</span>
            </div>
            <p className="panel-summary">{selectedDetail?.hypotheses[0]?.title ?? 'No hypotheses yet.'}</p>
            <div className="panel-body">
              {selectedDetail?.hypotheses.map((hypothesis) => (
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
              <span>{selectedDetail?.actions.length ?? 0}</span>
            </div>
            <p className="panel-summary">{nextAction?.description ?? 'No action selected.'}</p>
            <div className="panel-body">
              {selectedDetail?.actions.map((action) => (
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
              <span>{detail?.verification.status ?? selectedDetail?.verification.status ?? 'Pending'}</span>
            </div>
            <p className="panel-summary">{verificationSummary}</p>
            <div className="panel-body">
              <p className="lead">{detail?.verification.summary ?? selectedDetail?.verification.summary}</p>
              <div className="signal-list">
                {(detail?.verification.signals ?? selectedDetail?.verification.signals ?? []).map((signal) => <span key={signal}>{signal}</span>)}
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
            <p className="panel-summary">{selectedDetail?.report.summary ?? 'No report selected.'}</p>
            <div className="panel-body">
              <p className="lead">{selectedDetail?.report.summary}</p>
              <p className="next-step">{selectedDetail?.report.recommended_next_step}</p>
            </div>
          </article>
        </section>
      </section>
    </main>
  );
}
