import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import App from './App';

afterEach(() => {
  vi.restoreAllMocks();
});

const fleetResponse = {
  generated_at: '2026-07-07T03:05:00+00:00',
  summary: { total: 1, healthy: 0, warning: 1, critical: 0, stale: 0 },
  devices: [
    {
      device: {
        device_id: 'xps-13',
        hostname: 'build-xps',
        model: 'Dell XPS 13',
        os_name: 'Fedora 42',
        kernel_version: '6.14.4',
        first_seen_at: '2026-07-07T02:55:00+00:00',
        last_seen_at: '2026-07-07T03:04:00+00:00',
      },
      latest_metrics: {
        'cpu.package_temp_c': { value: 86.4, unit: 'celsius', observed_at: '2026-07-07T03:00:00+00:00' },
        'cpu.load_1m': { value: 3.7, unit: 'load', observed_at: '2026-07-07T03:00:00+00:00' },
        'nvme.temp_c': { value: 42.9, unit: 'celsius', observed_at: '2026-07-07T03:00:00+00:00' },
        'memory.used_percent': { value: 62.0, unit: 'percent', observed_at: '2026-07-07T03:00:00+00:00' },
        'wifi.signal_dbm': { value: -43.0, unit: 'dbm', observed_at: '2026-07-07T03:00:00+00:00' },
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
    summary: 'build-xps needs investigation for thermal evidence.',
    recommended_next_step: 'Inspect thermal evidence and compare cooling or workload windows.',
  },
  fleet_context: fleetResponse.devices[0],
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
    expect(screen.queryByText('Creator and visual references')).not.toBeInTheDocument();
    expect(screen.queryByText('Dogu Robotics · Dogu X · Physical AI')).not.toBeInTheDocument();
    expect(screen.getByText('About: workstation health investigation')).toBeInTheDocument();
    expect(screen.getByText('Version v0.7.0')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Explain CPU package temperature metric' })).toBeInTheDocument());
    expect(screen.getByText('정의: 선택한 장비의 CPU 패키지 센서 온도입니다. (CPU package temperature)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Explain 1 minute load average metric' })).toBeInTheDocument();
    expect(screen.getByText('정의: 최근 1분 동안 실행 중이거나 대기 중인 작업 평균입니다. (1-minute load average)')).toBeInTheDocument();
    expect(screen.getByText('해석: CPU 코어 수와 온도 추세를 함께 봐야 과부하인지 판단할 수 있습니다.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Explain Wi-Fi signal strength metric' })).toBeInTheDocument();
    expect(screen.getByText('정의: 무선 연결의 수신 신호 강도입니다. (Wi-Fi signal strength, dBm)')).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Telemetry coverage matrix' })).toBeInTheDocument();
    expect(screen.getAllByText('Wi-Fi Signal').length).toBeGreaterThan(0);
    expect(screen.getAllByText('-43 dBm').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Memory Used').length).toBeGreaterThan(0);
    expect(screen.getAllByText('62.0%').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Network Events').length).toBeGreaterThan(0);
    expect(screen.getAllByText('1 warning').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Kernel Warnings').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Thermal Throttling').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Reconnect History').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Disk Health').length).toBeGreaterThan(0);
    expect(screen.getAllByText('78.2%').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Battery Power').length).toBeGreaterThan(0);
    expect(screen.getAllByText('37.0%').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Fan RPM').length).toBeGreaterThan(0);
    expect(screen.getAllByText('2840 rpm').length).toBeGreaterThan(0);
    expect(screen.getAllByText('NVMe Health').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Critical warning').length).toBeGreaterThan(0);
    expect(screen.getAllByText('build-xps').length).toBeGreaterThan(0);
    expect(screen.getByText('Top hypotheses')).toBeInTheDocument();
    expect(screen.getByText('Action plan')).toBeInTheDocument();
    expect(screen.getByText('Recorded interventions')).toBeInTheDocument();
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
  });
});
