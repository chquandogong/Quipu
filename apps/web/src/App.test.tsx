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
      },
      recent_events: [],
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
      summary: 'CPU thermal threshold event reported during compile workload.',
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

    render(<App />);

    await waitFor(() => expect(screen.getByText('Investigation Queue')).toBeInTheDocument());
    expect(screen.getByText('Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report')).toBeInTheDocument();
    expect(screen.getByText('build-xps')).toBeInTheDocument();
    expect(screen.getByText('Top hypotheses')).toBeInTheDocument();
    expect(screen.getByText('Action plan')).toBeInTheDocument();
    expect(screen.getByText('Recorded interventions')).toBeInTheDocument();
    expect(screen.getByText('Verification')).toBeInTheDocument();
    await waitFor(() => expect(screen.getAllByText('-17.4C').length).toBeGreaterThan(0));
    expect(screen.getAllByText('Report').length).toBeGreaterThan(0);
    await waitFor(() => expect(screen.getByText('Check cooling and workload')).toBeInTheDocument());

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
