import '@testing-library/jest-dom/vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import App from './App';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('App', () => {
  it('renders fleet devices from the API', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        json: async () => ({
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
        }),
      })),
    );

    render(<App />);

    await waitFor(() => expect(screen.getByText('build-xps')).toBeInTheDocument());
    expect(screen.getByText('Warning')).toBeInTheDocument();
    expect(screen.getByText('CPU package temperature is elevated')).toBeInTheDocument();
  });
});
