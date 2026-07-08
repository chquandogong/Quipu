import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import App from './App';

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

const fleetResponse = {
  generated_at: '2026-07-07T03:05:00+00:00',
  summary: { total: 1, healthy: 0, warning: 1, critical: 0, stale: 0 },
  devices: [
    {
      device: {
        device_id: 'xps-13',
        display_name: 'Build laptop',
        hostname: 'build-xps',
        model: 'Dell XPS 13',
        cpu_model: 'Intel(R) Core(TM) Ultra 5 125H',
        os_name: 'Fedora 42',
        kernel_version: '6.14.4',
        first_seen_at: '2026-07-07T02:55:00+00:00',
        last_seen_at: '2026-07-07T03:04:00+00:00',
      },
      latest_metrics: {
        'cpu.package_temp_c': { value: 86.4, unit: 'celsius', observed_at: '2026-07-07T03:00:00+00:00' },
        'cpu.load_1m': { value: 3.7, unit: 'load', observed_at: '2026-07-07T03:00:00+00:00' },
        'cpu.load_5m': { value: 2.1, unit: 'load', observed_at: '2026-07-07T03:00:00+00:00' },
        'cpu.load_15m': { value: 0.9, unit: 'load', observed_at: '2026-07-07T03:00:00+00:00' },
        'cpu.physical_cores': { value: 14, unit: 'count', observed_at: '2026-07-07T03:00:00+00:00' },
        'cpu.logical_threads': { value: 18, unit: 'count', observed_at: '2026-07-07T03:00:00+00:00' },
        'cpu.performance_cores': { value: 4, unit: 'count', observed_at: '2026-07-07T03:00:00+00:00' },
        'cpu.efficient_cores': { value: 8, unit: 'count', observed_at: '2026-07-07T03:00:00+00:00' },
        'cpu.low_power_efficient_cores': { value: 2, unit: 'count', observed_at: '2026-07-07T03:00:00+00:00' },
        'cpu.core_0.temp_c': { value: 84.0, unit: 'celsius', observed_at: '2026-07-07T03:00:00+00:00' },
        'cpu.core_1.temp_c': { value: 82.5, unit: 'celsius', observed_at: '2026-07-07T03:00:00+00:00' },
        'cpu.core_3.temp_c': { value: 81.5, unit: 'celsius', observed_at: '2026-07-07T03:00:00+00:00' },
        'nvme.temp_c': { value: 42.9, unit: 'celsius', observed_at: '2026-07-07T03:00:00+00:00' },
        'nvme.nvme0.temp_c': { value: 42.9, unit: 'celsius', observed_at: '2026-07-07T03:00:00+00:00' },
        'nvme.nvme1.temp_c': { value: 44.2, unit: 'celsius', observed_at: '2026-07-07T03:00:00+00:00' },
        'nvme.capacity_bytes': { value: 512110190592, unit: 'bytes', observed_at: '2026-07-07T03:00:00+00:00' },
        'nvme.nvme0n1.capacity_bytes': { value: 512110190592, unit: 'bytes', observed_at: '2026-07-07T03:00:00+00:00' },
        'nvme.read_bytes_per_sec': { value: 12582912, unit: 'bytes_per_sec', observed_at: '2026-07-07T03:00:00+00:00' },
        'nvme.write_bytes_per_sec': { value: 4194304, unit: 'bytes_per_sec', observed_at: '2026-07-07T03:00:00+00:00' },
        'nvme.nvme0n1.read_bytes_per_sec': { value: 12582912, unit: 'bytes_per_sec', observed_at: '2026-07-07T03:00:00+00:00' },
        'nvme.nvme0n1.write_bytes_per_sec': { value: 4194304, unit: 'bytes_per_sec', observed_at: '2026-07-07T03:00:00+00:00' },
        'memory.used_percent': { value: 62.0, unit: 'percent', observed_at: '2026-07-07T03:00:00+00:00' },
        'wifi.signal_dbm': { value: -43.0, unit: 'dbm', observed_at: '2026-07-07T03:00:00+00:00' },
        'wifi.wlp0s20f3.signal_dbm': { value: -43.0, unit: 'dbm', observed_at: '2026-07-07T03:00:00+00:00' },
        'wifi.wlan0.signal_dbm': { value: -61.0, unit: 'dbm', observed_at: '2026-07-07T03:00:00+00:00' },
        'wifi.rx_bitrate_mbps': { value: 866.7, unit: 'mbps', observed_at: '2026-07-07T03:00:00+00:00' },
        'wifi.tx_bitrate_mbps': { value: 144.4, unit: 'mbps', observed_at: '2026-07-07T03:00:00+00:00' },
        'wifi.wlp0s20f3.rx_bitrate_mbps': { value: 866.7, unit: 'mbps', observed_at: '2026-07-07T03:00:00+00:00' },
        'wifi.wlp0s20f3.tx_bitrate_mbps': { value: 144.4, unit: 'mbps', observed_at: '2026-07-07T03:00:00+00:00' },
        'wifi.wlan0.rx_bitrate_mbps': { value: 72.2, unit: 'mbps', observed_at: '2026-07-07T03:00:00+00:00' },
        'wifi.wlan0.tx_bitrate_mbps': { value: 58.5, unit: 'mbps', observed_at: '2026-07-07T03:00:00+00:00' },
        'disk.root_used_percent': { value: 78.2, unit: 'percent', observed_at: '2026-07-07T03:00:00+00:00' },
        'battery.capacity_percent': { value: 37.0, unit: 'percent', observed_at: '2026-07-07T03:00:00+00:00' },
        'battery.ac_online': { value: 0.0, unit: 'boolean', observed_at: '2026-07-07T03:00:00+00:00' },
        'fan.rpm': { value: 2840.0, unit: 'rpm', observed_at: '2026-07-07T03:00:00+00:00' },
        'nvme.critical_warning': { value: 1.0, unit: 'boolean', observed_at: '2026-07-07T03:00:00+00:00' },
        'nvme.available_spare_percent': { value: 9.0, unit: 'percent', observed_at: '2026-07-07T03:00:00+00:00' },
        'nvme.percentage_used_percent': { value: 12.0, unit: 'percent', observed_at: '2026-07-07T03:00:00+00:00' },
        'nvme.media_errors': { value: 2.0, unit: 'count', observed_at: '2026-07-07T03:00:00+00:00' },
      },
      recent_events: [
        {
          category: 'network',
          severity: 'warning',
          source: 'NetworkManager',
          message_summary: 'Wi-Fi reconnect observed within the incident window.',
          raw_ref: 'journalctl -u NetworkManager',
          observed_at: '2026-07-07T02:57:20+00:00',
          fingerprint: 'xps-wifi-reconnect',
        },
      ],
      risk_level: 'warning',
      findings: [
        {
          category: 'thermal',
          title: 'CPU package temperature is elevated',
          evidence: 'Latest CPU package temperature is 86.4C.',
          confidence: 'medium',
        },
      ],
    },
  ],
};

const queueResponse = {
  items: [
    {
      id: 'xps-13:thermal',
      priority: 'Medium',
      stage: 'Triage',
      risk_level: 'warning',
      device_id: 'xps-13',
      device_display_name: 'Build laptop',
      device_hostname: 'build-xps',
      title: 'CPU package temperature is elevated',
      category: 'thermal',
      confidence: 'medium',
      why_now: 'CPU package temperature is elevated',
      evidence: 'Latest CPU package temperature is 86.4C.',
      next_step: 'Inspect thermal evidence and compare cooling or workload windows.',
      updated_at: '2026-07-07T03:05:00+00:00',
    },
  ],
};

const detailResponse = {
  item: queueResponse.items[0],
  timeline: [
    {
      observed_at: '2026-07-07T03:00:00+00:00',
      category: 'thermal',
      severity: 'warning',
      source: 'kernel',
      summary: 'CPU0: Core temperature above threshold, cpu clock throttled during compile workload.',
      raw_ref: 'journalctl -k',
    },
    {
      observed_at: '2026-07-07T02:57:20+00:00',
      category: 'network',
      severity: 'warning',
      source: 'NetworkManager',
      summary: 'Wi-Fi reconnect observed within the incident window.',
      raw_ref: 'journalctl -u NetworkManager',
    },
    {
      observed_at: '2026-07-07T02:55:10+00:00',
      category: 'storage',
      severity: 'warning',
      source: 'kernel',
      summary: 'nvme0n1: I/O timeout, reset controller',
      raw_ref: 'journalctl -k',
    },
    {
      observed_at: '2026-07-07T02:54:00+00:00',
      category: 'power',
      severity: 'warning',
      source: 'kernel',
      summary: 'ACPI: battery discharge rate high while AC offline',
      raw_ref: 'journalctl -k',
    },
  ],
  hypotheses: [
    {
      category: 'thermal',
      title: 'CPU package temperature is elevated',
      confidence: 'medium',
      supporting_evidence: ['Latest CPU package temperature is 86.4C.'],
      contradicting_evidence: ['No before/after intervention window has been recorded yet.'],
      missing_checks: ['Inspect thermal evidence and compare cooling or workload windows.'],
    },
  ],
  actions: [
    {
      label: 'Check cooling and workload',
      description: 'Record physical cooling changes and compare load-adjusted temperatures.',
    },
  ],
  interventions: [
    {
      id: 1,
      investigation_id: 'xps-13:thermal',
      device_id: 'xps-13',
      category: 'thermal',
      label: 'Raised rear edge',
      description: 'Lifted one side of the laptop to improve bottom airflow.',
      expected_effect: 'Temperature should drop in the next observation window.',
      recorded_at: '2026-07-07T03:05:00+00:00',
      verification_status: 'pending',
      verification_result: {
        status: 'helped',
        summary: 'CPU package temperature fell by 17.4C after Raised rear edge.',
        window_minutes: 30,
        checks: [
          {
            name: 'CPU package temperature',
            before: '86.4C',
            after: '69.0C',
            delta: '-17.4C',
            verdict: 'improved',
          },
        ],
      },
    },
  ],
  verification: {
    status: 'Helped',
    summary: 'CPU package temperature fell by 17.4C after Raised rear edge.',
    signals: ['CPU package temperature', 'Warning recurrence', '1 minute load average'],
  },
  report: {
    summary: 'Build laptop needs investigation for thermal evidence.',
    recommended_next_step: 'Inspect thermal evidence and compare cooling or workload windows.',
  },
  fleet_context: fleetResponse.devices[0],
};

const patternResponse = {
  category_groups: [
    {
      category: 'thermal',
      count: 2,
      device_count: 1,
      severities: { info: 0, warning: 2, critical: 0 },
      latest_observed_at: '2026-07-07T03:00:00+00:00',
      examples: [],
    },
  ],
  model_groups: [
    {
      model: 'Dell XPS 13',
      count: 2,
      device_count: 1,
      severities: { info: 0, warning: 2, critical: 0 },
      latest_observed_at: '2026-07-07T03:00:00+00:00',
      examples: [],
    },
  ],
  kernel_groups: [
    {
      kernel_version: '6.14.4',
      count: 2,
      device_count: 1,
      severities: { info: 0, warning: 2, critical: 0 },
      latest_observed_at: '2026-07-07T03:00:00+00:00',
      examples: [],
    },
  ],
  component_groups: [
    {
      component: 'gpu:i915',
      count: 2,
      device_count: 1,
      severities: { info: 0, warning: 2, critical: 0 },
      latest_observed_at: '2026-07-07T03:00:00+00:00',
      examples: [],
    },
  ],
};

const notesResponse = {
  notes: [
    {
      id: 1,
      investigation_id: 'xps-13:thermal',
      author: 'ops',
      body: 'Raised the rear edge and will compare the next two batches.',
      created_at: '2026-07-07T03:07:00+00:00',
    },
  ],
};

describe('App', () => {
  it('renders the investigation workflow as the primary surface', async () => {
    const createdIntervention = {
      id: 2,
      investigation_id: 'xps-13:thermal',
      device_id: 'xps-13',
      category: 'thermal',
      label: 'Raised rear edge',
      description: 'Lifted one side of the laptop to improve bottom airflow.',
      expected_effect: 'Temperature should drop in the next observation window.',
      recorded_at: '2026-07-07T03:05:00+00:00',
      verification_status: 'pending',
    };
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith('/api/fleet/overview')) {
        return { ok: true, json: async () => fleetResponse };
      }
      if (url.endsWith('/api/investigations/queue')) {
        return { ok: true, json: async () => queueResponse };
      }
      if (url.endsWith('/api/patterns/overview')) {
        return { ok: true, json: async () => patternResponse };
      }
      if (url.endsWith('/api/investigations/xps-13%3Athermal/notes') && init?.method === 'POST') {
        return {
          ok: true,
          json: async () => ({
            id: 2,
            investigation_id: 'xps-13:thermal',
            author: 'ops',
            body: 'Thermal result handed off to the next operator.',
            created_at: '2026-07-07T03:09:00+00:00',
          }),
        };
      }
      if (url.endsWith('/api/investigations/xps-13%3Athermal/notes')) {
        return { ok: true, json: async () => notesResponse };
      }
      if (url.endsWith('/api/investigations/xps-13%3Athermal/interventions') && init?.method === 'POST') {
        return { ok: true, json: async () => createdIntervention };
      }
      if (url.endsWith('/api/investigations/xps-13%3Athermal')) {
        return { ok: true, json: async () => detailResponse };
      }
      throw new Error(`unexpected URL ${url}`);
    });

    vi.stubGlobal(
      'fetch',
      fetchMock,
    );

    const { container } = render(<App />);

    await waitFor(() => expect(screen.getByText('Investigation Queue')).toBeInTheDocument());
    expect(container.querySelector('.page-command-dark')).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Investigation command center' })).toBeInTheDocument();
    expect(screen.getByText('Inspect now')).toBeInTheDocument();
    expect(screen.getByText('지금 확인')).toBeInTheDocument();
    expect(screen.getByText('Why it matters')).toBeInTheDocument();
    expect(screen.getByText('판단 근거')).toBeInTheDocument();
    expect(screen.getByText('Do next')).toBeInTheDocument();
    expect(screen.getByText('다음 행동')).toBeInTheDocument();
    expect(screen.getByText('Proof needed')).toBeInTheDocument();
    expect(screen.getByText('검증 조건')).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Problem guide' })).toBeInTheDocument();
    expect(screen.getByText('뭐가 문제지?')).toBeInTheDocument();
    expect(screen.getByText('그래서 뭘 해야 하지?')).toBeInTheDocument();
    expect(screen.getByText('먼저 볼 근거')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('region', { name: 'Telemetry Brief' })).toBeInTheDocument());
    expect(screen.getByText('Telemetry Brief')).toBeInTheDocument();
    expect(container.querySelector('.signal-console')).not.toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Workflow rail' })).toBeInTheDocument();
    expect(screen.getByText('Triage -> Investigate')).toBeInTheDocument();
    const workflowRail = screen.getByRole('region', { name: 'Workflow rail' });
    const stageList = within(workflowRail).getByRole('list', { name: 'DTIHAVR stages' });
    expect(within(stageList).getByText('D')).toBeInTheDocument();
    expect(within(stageList).getByText('T')).toBeInTheDocument();
    expect(within(stageList).getByText('I')).toBeInTheDocument();
    expect(within(stageList).getByText('H')).toBeInTheDocument();
    expect(within(stageList).getByText('A')).toBeInTheDocument();
    expect(within(stageList).getByText('V')).toBeInTheDocument();
    expect(within(stageList).getByText('R')).toBeInTheDocument();
    expect(within(stageList).getByText('Detect')).toBeInTheDocument();
    expect(within(stageList).getByText('Report')).toBeInTheDocument();
    expect(container.querySelector('.stage-strip')).not.toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Fleet Brief' })).toBeInTheDocument();
    const fleetBrief = screen.getByRole('region', { name: 'Fleet Brief' });
    expect(screen.getByText('Fleet Brief')).toBeInTheDocument();
    expect(within(fleetBrief).getByLabelText('Total devices: 1')).toBeInTheDocument();
    expect(within(fleetBrief).getByLabelText('Critical devices: 0')).toBeInTheDocument();
    expect(within(fleetBrief).getByLabelText('Warning devices: 1')).toBeInTheDocument();
    expect(within(fleetBrief).getByLabelText('Queue cases: 1')).toBeInTheDocument();
    expect(within(fleetBrief).getByText('Total은 현재 fleet에서 관측된 장비 수입니다.')).toBeInTheDocument();
    expect(within(fleetBrief).getByText('Queue는 지금 조사 queue에 올라온 case 수입니다. 장비 수와 다를 수 있습니다.')).toBeInTheDocument();
    expect(screen.getByText('Warning source')).toBeInTheDocument();
    expect(screen.getByText('Build laptop · build-xps / thermal')).toBeInTheDocument();
    expect(container.querySelector('.health-strip')).not.toBeInTheDocument();
    expect(container.querySelector('.metric-strip')).not.toBeInTheDocument();
    expect(container.querySelector('.metric-card')).not.toBeInTheDocument();
    expect(screen.queryByText('Creator and visual references')).not.toBeInTheDocument();
    expect(screen.queryByText('Dogu Robotics · Dogu X · Physical AI')).not.toBeInTheDocument();
    expect(screen.getByText('Project info')).toBeInTheDocument();
    expect(screen.getByText('Made by Dr. 권성호')).toBeInTheDocument();
    expect(screen.getByText('About: workstation health investigation')).toBeInTheDocument();
    expect(screen.getByText('Version v0.12.0')).toBeInTheDocument();
    expect(screen.queryByText('Detect - triage - verify with evidence')).not.toBeInTheDocument();
    expect(screen.getAllByText('Build laptop · build-xps').length).toBeGreaterThan(0);
    const selectedCaseStatus = screen.getByLabelText('Selected case status');
    expect(screen.getByText('Priority / 우선순위')).toBeInTheDocument();
    expect(within(selectedCaseStatus).getByText('Medium').closest('.status-chip')).toHaveClass('priority-medium');
    expect(screen.getByText('Medium은 지금 queue에 남겨 확인할 항목이지만 즉시 장애 수준은 아니라는 뜻입니다.')).toBeInTheDocument();
    expect(screen.getByText('Risk level / 위험도')).toBeInTheDocument();
    expect(screen.getByText('Warning · thermal')).toBeInTheDocument();
    expect(within(selectedCaseStatus).getByText('Warning · thermal').closest('.status-chip')).toHaveClass('risk-warning');
    expect(screen.getByText('Warning은 경고 근거가 있어 확인이 필요하다는 뜻입니다. Critical은 더 높은 위험, Stale은 데이터가 오래됨입니다.')).toBeInTheDocument();
    expect(screen.getByText('선택된 warning 출처: Build laptop · build-xps / thermal - CPU package temperature is elevated.')).toBeInTheDocument();
    expect(screen.getByText('Workflow stage / 진행 단계')).toBeInTheDocument();
    expect(screen.getAllByText('Triage는 감지된 근거를 분류하고 다음 조사 항목을 고르는 단계입니다.').length).toBeGreaterThan(0);
    expect(screen.getByRole('region', { name: 'Operations Rail' })).toBeInTheDocument();
    expect(screen.getByText('Offline Buffer')).toBeInTheDocument();
    expect(screen.getByText('Enrollment Guard')).toBeInTheDocument();
    expect(screen.getByText('Pattern Radar')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Explain CPU package temperature metric' })).toBeInTheDocument());
    expect(screen.getByText('정의: 선택한 장비의 CPU 패키지 센서 온도입니다. (CPU package temperature)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Explain Linux load average windows metric' })).toBeInTheDocument();
    expect(screen.getByText('정의: 최근 1/5/15분 동안 실행 중이거나 대기 중인 작업 평균입니다. (Linux load average)')).toBeInTheDocument();
    expect(screen.getByText('해석: CPU 코어 수와 온도 추세를 함께 봐야 과부하인지 판단할 수 있습니다.')).toBeInTheDocument();
    expect(screen.queryByText('Cores: core 0 84.0C · core 1 82.5C')).not.toBeInTheDocument();
    const cpuCore0 = screen.getByLabelText('CPU core 0 temperature: 84.0C');
    const cpuCore1 = screen.getByLabelText('CPU core 1 temperature: 82.5C');
    const cpuCore3 = screen.getByLabelText('CPU core 3 temperature: 81.5C');
    expect(cpuCore0).toHaveClass('breakdown-watch');
    expect(cpuCore1).toHaveClass('breakdown-watch');
    expect(cpuCore3).toHaveClass('breakdown-watch');
    expect(cpuCore0).toHaveTextContent('0');
    expect(cpuCore0).toHaveTextContent('84.0C');
    expect(cpuCore1).toHaveTextContent('1');
    expect(cpuCore1).toHaveTextContent('82.5C');
    expect(screen.queryByLabelText('CPU core 2 temperature: -')).not.toBeInTheDocument();
    expect(cpuCore3).toHaveTextContent('3');
    expect(cpuCore3).toHaveTextContent('81.5C');
    expect(screen.queryByText('Windows: 1m 3.70 · 5m 2.10 · 15m 0.90')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Load average 1m: 3.70')).toHaveClass('breakdown-nominal');
    expect(screen.getByLabelText('Load average 5m: 2.10')).toHaveClass('breakdown-nominal');
    expect(screen.getByLabelText('Load average 15m: 0.90')).toHaveClass('breakdown-nominal');
    expect(screen.queryByText('Devices: nvme0 42.9C · nvme1 44.2C')).not.toBeInTheDocument();
    expect(screen.getByLabelText('NVMe nvme0n1: 42.9C · 477 GB · R 12 MB/s · W 4 MB/s')).toHaveClass('breakdown-nominal');
    expect(screen.getByLabelText('NVMe nvme1: 44.2C')).toHaveClass('breakdown-nominal');
    expect(screen.queryByText('Interfaces: wlp0s20f3 -43 dBm · wlan0 -61 dBm')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Wi-Fi wlp0s20f3: -43 dBm · Rx 867 Mbps · Tx 144 Mbps')).toHaveClass('breakdown-nominal');
    expect(screen.getByLabelText('Wi-Fi wlan0: -61 dBm · Rx 72.2 Mbps · Tx 58.5 Mbps')).toHaveClass('breakdown-nominal');
    expect(screen.getByRole('button', { name: 'Explain Wi-Fi signal strength metric' })).toBeInTheDocument();
    expect(screen.getByText('정의: 무선 연결의 수신 신호 강도입니다. (Wi-Fi signal strength, dBm)')).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Telemetry coverage matrix' })).toBeInTheDocument();
    const telemetryMatrix = screen.getByRole('region', { name: 'Telemetry coverage matrix' });
    expect(within(telemetryMatrix).getByText('14/14 observed')).toBeInTheDocument();
    expect(within(telemetryMatrix).getByText('관측된 범주 수입니다. 위험 점수가 아니라, 조사에 필요한 자료가 얼마나 들어왔는지 보여줍니다.')).toBeInTheDocument();
    expect(within(telemetryMatrix).getByText('Missing: none')).toBeInTheDocument();
    expect(screen.getAllByText('Wi-Fi Signal').length).toBeGreaterThan(0);
    expect(screen.getAllByText('-43 dBm').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Memory Used').length).toBeGreaterThan(0);
    expect(screen.getAllByText('62.0%').length).toBeGreaterThan(0);
    expect(screen.getAllByText('CPU Profile').length).toBeGreaterThan(0);
    expect(screen.getAllByText('14 cores / 18 threads').length).toBeGreaterThan(0);
    expect(screen.getByText('Intel Core Ultra 5 125H. Topology: P 4, E 8, LP-E 2.')).toBeInTheDocument();
    expect(screen.getAllByText('Wi-Fi Link').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Rx 867 Mbps / Tx 144 Mbps').length).toBeGreaterThan(0);
    expect(screen.getAllByText('NVMe Capacity').length).toBeGreaterThan(0);
    expect(screen.getAllByText('477 GB').length).toBeGreaterThan(0);
    expect(screen.getAllByText('NVMe I/O').length).toBeGreaterThan(0);
    expect(screen.getAllByText('R 12 MB/s / W 4 MB/s').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Network Events').length).toBeGreaterThan(0);
    expect(within(telemetryMatrix).getByText('1 network event')).toBeInTheDocument();
    expect(screen.getAllByText('Kernel Warnings').length).toBeGreaterThan(0);
    expect(within(telemetryMatrix).getByText('3 kernel events')).toBeInTheDocument();
    expect(screen.getAllByText('Thermal Throttling').length).toBeGreaterThan(0);
    expect(within(telemetryMatrix).getByText('1 thermal event')).toBeInTheDocument();
    expect(screen.getAllByText('Reconnect History').length).toBeGreaterThan(0);
    expect(within(telemetryMatrix).getByText('1 reconnect event')).toBeInTheDocument();
    expect(screen.getAllByText('Disk Health').length).toBeGreaterThan(0);
    expect(screen.getAllByText('78.2%').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Battery Power').length).toBeGreaterThan(0);
    expect(screen.getAllByText('37.0%').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Fan RPM').length).toBeGreaterThan(0);
    expect(screen.getAllByText('2840 rpm').length).toBeGreaterThan(0);
    expect(screen.getAllByText('NVMe Health').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Critical warning').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Build laptop · build-xps/).length).toBeGreaterThan(0);
    expect(screen.getByText('Top hypotheses')).toBeInTheDocument();
    expect(screen.getByText('Action plan')).toBeInTheDocument();
    expect(screen.getByText('Recorded interventions')).toBeInTheDocument();
    expect(screen.getByText('Team Handoff')).toBeInTheDocument();
    expect(screen.getByText('Pattern Explorer')).toBeInTheDocument();
    expect(screen.getByText('By component')).toBeInTheDocument();
    expect(screen.getByText('gpu:i915')).toBeInTheDocument();
    expect(screen.getAllByText('Raised the rear edge and will compare the next two batches.').length).toBeGreaterThan(0);
    expect(screen.getByText('By category')).toBeInTheDocument();
    expect(screen.getAllByText('Verification').length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: 'Review evidence' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Record action' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Verify result' })).toBeInTheDocument();
    await waitFor(() => expect(screen.getAllByText('-17.4C').length).toBeGreaterThan(0));
    expect(screen.getAllByText('Report').length).toBeGreaterThan(0);
    await waitFor(() => expect(screen.getAllByText('Check cooling and workload').length).toBeGreaterThan(0));

    fireEvent.change(screen.getByLabelText('Intervention label'), { target: { value: 'Raised rear edge' } });
    fireEvent.change(screen.getByLabelText('Intervention description'), {
      target: { value: 'Lifted one side of the laptop to improve bottom airflow.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Record intervention' }));

    await waitFor(() => expect(screen.getAllByText('Raised rear edge').length).toBeGreaterThan(0));
    const postCall = fetchMock.mock.calls.find(([input, init]) => String(input).includes('/interventions') && init?.method === 'POST');
    expect(postCall).toBeDefined();
    expect(JSON.parse(String(postCall?.[1]?.body)).label).toBe('Raised rear edge');

    fireEvent.change(screen.getByLabelText('Handoff note'), {
      target: { value: 'Thermal result handed off to the next operator.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Record handoff' }));

    await waitFor(() => expect(screen.getByText('Thermal result handed off to the next operator.')).toBeInTheDocument());
    const notePostCall = fetchMock.mock.calls.find(([input, init]) => String(input).includes('/notes') && init?.method === 'POST');
    expect(notePostCall).toBeDefined();
    expect(JSON.parse(String(notePostCall?.[1]?.body)).body).toBe('Thermal result handed off to the next operator.');
  });

  it('groups Intel Core Ultra 5 125H core sensors by core type', async () => {
    const {
      'cpu.core_0.temp_c': _core0,
      'cpu.core_1.temp_c': _core1,
      'cpu.core_3.temp_c': _core3,
      ...latestMetricsWithoutCores
    } = detailResponse.fleet_context.latest_metrics;
    const ultraCoreMetrics = Object.fromEntries(
      [0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 20, 32, 33].map((coreId) => [
        `cpu.core_${coreId}.temp_c`,
        { value: 50 + coreId / 10, unit: 'celsius', observed_at: '2026-07-07T03:00:00+00:00' },
      ]),
    );
    const detailWithUltraCores = {
      ...detailResponse,
      fleet_context: {
        ...detailResponse.fleet_context,
        latest_metrics: {
          ...latestMetricsWithoutCores,
          ...ultraCoreMetrics,
        },
      },
    };
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/api/fleet/overview')) {
        return { ok: true, json: async () => fleetResponse };
      }
      if (url.endsWith('/api/investigations/queue')) {
        return { ok: true, json: async () => queueResponse };
      }
      if (url.endsWith('/api/patterns/overview')) {
        return { ok: true, json: async () => patternResponse };
      }
      if (url.endsWith('/api/investigations/xps-13%3Athermal/notes')) {
        return { ok: true, json: async () => notesResponse };
      }
      if (url.endsWith('/api/investigations/xps-13%3Athermal')) {
        return { ok: true, json: async () => detailWithUltraCores };
      }
      throw new Error(`unexpected URL ${url}`);
    });

    vi.stubGlobal('fetch', fetchMock);
    render(<App />);

    await waitFor(() => expect(screen.getByLabelText('P core group: 8 50.8C, 12 51.2C, 16 51.6C, 20 52.0C')).toBeInTheDocument());
    expect(screen.getByLabelText('E core group: 0 50.0C, 1 50.1C, 2 50.2C, 3 50.3C, 4 50.4C, 5 50.5C, 6 50.6C, 7 50.7C')).toBeInTheDocument();
    expect(screen.getByLabelText('LP-E core group: 32 53.2C, 33 53.3C')).toBeInTheDocument();
    expect(screen.getByLabelText('CPU P core 8 temperature: 50.8C')).toHaveTextContent('8');
    expect(screen.getByLabelText('CPU E core 0 temperature: 50.0C')).toHaveTextContent('0');
    expect(screen.getByLabelText('CPU LP-E core 32 temperature: 53.2C')).toHaveTextContent('32');
  });

  it('shows an explicit CPU core sensor absence state', async () => {
    const {
      'cpu.core_0.temp_c': _core0,
      'cpu.core_1.temp_c': _core1,
      'cpu.core_3.temp_c': _core3,
      ...latestMetrics
    } = detailResponse.fleet_context.latest_metrics;
    const detailWithoutCoreMetrics = {
      ...detailResponse,
      fleet_context: {
        ...detailResponse.fleet_context,
        latest_metrics: latestMetrics,
      },
    };
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/api/fleet/overview')) {
        return { ok: true, json: async () => fleetResponse };
      }
      if (url.endsWith('/api/investigations/queue')) {
        return { ok: true, json: async () => queueResponse };
      }
      if (url.endsWith('/api/patterns/overview')) {
        return { ok: true, json: async () => patternResponse };
      }
      if (url.endsWith('/api/investigations/xps-13%3Athermal/notes')) {
        return { ok: true, json: async () => notesResponse };
      }
      if (url.endsWith('/api/investigations/xps-13%3Athermal')) {
        return { ok: true, json: async () => detailWithoutCoreMetrics };
      }
      throw new Error(`unexpected URL ${url}`);
    });

    vi.stubGlobal('fetch', fetchMock);
    render(<App />);

    await waitFor(() => expect(screen.getByLabelText('CPU core temperatures: no per-core sensors reported')).toBeInTheDocument());
    expect(screen.getByText('No core sensors')).toBeInTheDocument();
    expect(screen.queryByLabelText('CPU core 0 temperature: 84.0C')).not.toBeInTheDocument();
  });
});
