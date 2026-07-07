export type RiskLevel = 'healthy' | 'warning' | 'critical' | 'stale';

export type Device = {
  device_id: string;
  hostname: string;
  model: string | null;
  os_name: string | null;
  kernel_version: string | null;
  first_seen_at: string;
  last_seen_at: string;
};

export type MetricSample = {
  value: number;
  unit: string;
  observed_at: string;
};

export type EventSummary = {
  category: string;
  severity: string;
  source: string;
  message_summary: string;
  raw_ref: string | null;
  observed_at: string;
  fingerprint: string;
};

export type Finding = {
  category: string;
  title: string;
  evidence: string;
  confidence: string;
};

export type DeviceSnapshot = {
  device: Device;
  latest_metrics: Record<string, MetricSample>;
  recent_events: EventSummary[];
  risk_level: RiskLevel;
  findings: Finding[];
};

export type FleetOverview = {
  generated_at: string;
  summary: {
    total: number;
    healthy: number;
    warning: number;
    critical: number;
    stale: number;
  };
  devices: DeviceSnapshot[];
};
