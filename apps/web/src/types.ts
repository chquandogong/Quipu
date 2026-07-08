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

export type InvestigationItem = {
  id: string;
  priority: 'High' | 'Medium' | 'Low';
  stage: string;
  risk_level: RiskLevel;
  device_id: string;
  device_hostname: string;
  title: string;
  category: string;
  confidence: string;
  why_now: string;
  evidence: string;
  next_step: string;
  updated_at: string;
};

export type InvestigationQueue = {
  items: InvestigationItem[];
};

export type TimelineEvent = {
  observed_at: string;
  category: string;
  severity: string;
  source: string;
  summary: string;
  raw_ref: string | null;
};

export type Hypothesis = {
  category: string;
  title: string;
  confidence: string;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  missing_checks: string[];
};

export type ActionSuggestion = {
  label: string;
  description: string;
};

export type VerificationSummary = {
  status: string;
  summary: string;
  signals: string[];
};

export type VerificationCheck = {
  name: string;
  before: string | null;
  after: string | null;
  delta: string | null;
  verdict: string;
};

export type VerificationResult = {
  status: 'helped' | 'worse' | 'unclear' | 'insufficient_data';
  summary: string;
  window_minutes: number;
  checks: VerificationCheck[];
};

export type InterventionRecord = {
  id: number;
  investigation_id: string;
  device_id: string;
  category: string;
  label: string;
  description: string;
  expected_effect: string | null;
  recorded_at: string;
  verification_status: string;
  verification_result?: VerificationResult;
};

export type InterventionCreate = {
  label: string;
  description: string;
  expected_effect?: string | null;
  recorded_at?: string;
};

export type InvestigationNote = {
  id: number;
  investigation_id: string;
  author: string;
  body: string;
  created_at: string;
};

export type InvestigationNoteCreate = {
  author: string;
  body: string;
  created_at?: string;
};

export type InvestigationNotes = {
  notes: InvestigationNote[];
};

export type PatternGroup = {
  category?: string;
  model?: string;
  kernel_version?: string;
  count: number;
  device_count: number;
  severities: {
    info: number;
    warning: number;
    critical: number;
  };
  latest_observed_at: string;
  examples: Array<{
    device_id: string;
    hostname: string;
    summary: string;
    observed_at: string;
  }>;
};

export type PatternOverview = {
  category_groups: PatternGroup[];
  model_groups: PatternGroup[];
  kernel_groups: PatternGroup[];
};

export type InvestigationDetail = {
  item: InvestigationItem;
  timeline: TimelineEvent[];
  hypotheses: Hypothesis[];
  actions: ActionSuggestion[];
  interventions: InterventionRecord[];
  verification: VerificationSummary;
  report: {
    summary: string;
    recommended_next_step: string;
  };
  fleet_context: DeviceSnapshot;
};
